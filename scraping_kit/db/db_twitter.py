from __future__ import annotations
from typing import Type, Dict, List, Tuple
from datetime import datetime
from pathlib import Path
from requests import Response

import pandas as pd
from bson import ObjectId
from pymongo.results import InsertOneResult
from pymongo.database import Database
from pymongo.collection import Collection

from scraping_kit.db.base import DBMongoBase, HOST_DEFAULT
from scraping_kit.bot_scraper import BotScraper, ReqArgs, BotList
from scraping_kit.db.models.raw import RawData
from scraping_kit.db.models.trends import Trends
from scraping_kit.utils import iter_dates_by_range, date_one_day
from scraping_kit.db.models.search import Search
from scraping_kit.db.models.topics import Topic


def format_yyyy_mm_dd(year: int, month: int, day: int) -> str:
    year, month, day = str(year).zfill(4), str(month).zfill(2), str(day).zfill(2)
    return f"{year}_{month}_{day}"

def format_date_yyyy_mm_dd(date: datetime) -> str:
    return format_yyyy_mm_dd(date.year, date.month, date.day)

def _get_accumulated_name(date_from: datetime, date_to: datetime) -> str:
    accumulated_name = "trends_"
    accumulated_name += f"from_{format_date_yyyy_mm_dd(date_from)}_"
    accumulated_name += f"to_{format_date_yyyy_mm_dd(date_to)}.csv"
    return accumulated_name

def _get_per_day_name(year: int, month: int, day: int) -> str:
    return f"trends_{format_yyyy_mm_dd(year, month, day)}.csv"


def insert_to_obj_id(insert_one_result: InsertOneResult | str) -> ObjectId:
    if isinstance(insert_one_result, str):
        insert_one_result = ObjectId(insert_one_result)
    elif isinstance(insert_one_result, InsertOneResult):
        insert_one_result = insert_one_result.inserted_id
    return insert_one_result


class DBTwitterColl:
    def __init__(self, db: Database):
        self.cache: Collection = db.get_collection("cache")
        self.raw: Collection = db.get_collection("raw")
        self.trends: Collection = db.get_collection("trends")
        self.topics: Collection = db.get_collection("topics")
        self.user: Collection = db.get_collection("user")
        self.user_suspended: Collection = db.get_collection("user_suspended")
        self.tweet: Collection = db.get_collection("tweet")
        self.cursors: Collection = db.get_collection("cursors")
        self.search: Collection = db.get_collection("search")

    def trends_from_insert_id(self, insert_one_result_trend: InsertOneResult | str) -> Trends | None:
        obj_id = insert_to_obj_id(insert_one_result_trend)
        trends_json = self.trends.find_one({"_id": obj_id})
        if trends_json is not None:
            return Trends(**trends_json)
    
    def trends_from_date_range(self, date_range: Dict[str, datetime]) -> Trends | None:
        trends_json = self.trends.find_one({"created": date_range})
        if trends_json is not None:
            return Trends(**trends_json)


    def change_is_processed(self, insert_one_result_raw: InsertOneResult | str) -> None:
        obj_id = insert_to_obj_id(insert_one_result_raw)
        self.raw.update_one({"_id": obj_id}, {"$set": {"is_processed": True}})

    def save_search(self, search: Search) -> None:
        self.search.insert_one(search.model_dump())

    def save_topic(self, topic: Topic) -> None:
        """ TODO: Este método podría ser genérico."""
        self.topics.insert_one(topic.model_dump())


class DBTwitter(DBMongoBase):
    def __init__(self, path_data: Path, db_name: str, host=HOST_DEFAULT):
        super().__init__(db_name=db_name, host=host)
        self.coll = DBTwitterColl(db = self.db)
        
        self.path_data = path_data
        self.path_reports_folder = self.path_data / "reports"
        self.path_reports_accumulated_folder = self.path_reports_folder / "trends_accumulated"
        self.path_reports_per_day_folder = self.path_reports_folder / "trends_per_day"
        self.path_backup_db = self.path_data / "backup_db"
        self.path_acc = self.path_data / "acc.json"
        self.__init_db()

    def add_raw_data(self, req_args: Type[ReqArgs], response: Response, creation_date: datetime) -> InsertOneResult:
        if 200 <= response.status_code <= 299:
            response_json = response.json()
            is_processed = False
        else:
            response_json = None
            is_processed = True
        
        raw_data = RawData(
            creation_date = creation_date,
            req_args = req_args.model_dump(),
            response_json = response_json,
            endpoint_name = req_args.endpoint_name(),
            is_processed = is_processed
        )
        insert_one_result = self.coll.raw.insert_one(raw_data.model_dump())
        return insert_one_result

    def get_trends_df_accumulated(
            self,
            date_from: datetime,
            date_to: datetime,
            with_save: bool = True) -> pd.DataFrame:
        dates_empty: List[datetime] = []
        dates_accumulated: List[datetime] = []
        df_accumulated = []
        for date in iter_dates_by_range(date_from=date_from, date_to=date_to):
            trends_date = self.coll.trends_from_date_range(date)
            if trends_date is not None:
                dates_accumulated.append(date["$gte"])
                df_accumulated.append(trends_date.get_df())
            else:
                dates_empty.append(date["$gte"])
        
        if len(dates_empty)!=0:
            dates_empty = [f"{str(d.day).zfill(2)}_{str(d.month).zfill(2)}" for d in dates_empty]
            txt_no_data = "Days without data: " + " ~ ".join(dates_empty)
            print(txt_no_data)


        df_accumulated = pd.concat(df_accumulated)
        def _consolidate_domain_context(group):
            DELIMITER = " | "
            domain_contexts = set(d.strip() for d in group if d.strip())
            return DELIMITER.join(domain_contexts)
        df_accumulated['domainContext'] = df_accumulated.groupby('name')['domainContext'].transform(_consolidate_domain_context)


        df_accumulated = df_accumulated.groupby(["name", "query", "url", "domainContext"], as_index=False)["volume"].sum()
        df_accumulated.sort_values(by="volume", ascending=False, inplace=True)
        df_accumulated.reset_index(drop=True, inplace=True)
        
        if with_save:
            date_from, date_to = dates_accumulated[0], dates_accumulated[-1]

            path_accumulated = self.path_reports_accumulated_folder / _get_accumulated_name(date_from, date_to)
            df_accumulated.to_csv(path_accumulated)
            print(f"Accumulated from: {format_date_yyyy_mm_dd(date_from)}")
            print(f"Accumulated to: {format_date_yyyy_mm_dd(date_to)}")
            print(f"File saved inside: {path_accumulated.name}")
        return df_accumulated

    def get_trends_df_per_day(
            self,
            year: int,
            month: int,
            day: int,
            with_save: bool = True) -> pd.DataFrame | None:
        date = date_one_day(year=year, month=month, day=day)
        trends = self.coll.trends_from_date_range(date)
        if trends is None:
            return None
        else:
            df_trends = trends.get_df()
        if with_save:
            path_df_per_day = self.path_reports_per_day_folder / _get_per_day_name(year, month, day)
            df_trends.to_csv(path_df_per_day)
        return df_trends


    def load_bots(self) -> BotList:
        return BotList.load_from_json(self.path_acc)

    def requests_and_save(self, req_args: Type[ReqArgs], bot: BotScraper) -> InsertOneResult:
        response, creation_date = self.requests(req_args, bot)
        insert_one_result_raw = self.add_raw_data(req_args, response, creation_date)
        return insert_one_result_raw

    def requests(self, req_args: Type[ReqArgs], bot: BotScraper) -> tuple[Response, datetime]:
        response, creation_date = bot.get_response(req_args)
        return response, creation_date

    def __init_db(self) -> None:
        self.path_data.mkdir(exist_ok=True)
        self.path_reports_folder.mkdir(exist_ok=True)
        self.path_reports_accumulated_folder.mkdir(exist_ok=True)
        self.path_reports_per_day_folder.mkdir(exist_ok=True)
        self.path_backup_db.mkdir(exist_ok=True)
    
