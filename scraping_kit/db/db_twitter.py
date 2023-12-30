from typing import Type, Dict
from datetime import datetime, timedelta
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
from scraping_kit.utils import iter_dates_delta_n_days_back


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
        self.user: Collection = db.get_collection("user")
        self.user_suspended: Collection = db.get_collection("user_suspended")
        self.tweet: Collection = db.get_collection("tweet")
        self.cursors: Collection = db.get_collection("cursors")

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

def _get_accumulated_name(date_from: datetime, date_to: datetime) -> str:
    accumulated_name = f"topics_from_{date_to.year}_{date_to.month}_{date_to.day}_"
    accumulated_name += f"to_{date_from.year}_{date_from.month}_{date_from.day}.csv"
    return accumulated_name

class DBTwitter(DBMongoBase):
    def __init__(self, path_data: Path, db_name: str, host=HOST_DEFAULT):
        super().__init__(db_name=db_name, host=host)
        self.coll = DBTwitterColl(db = self.db)
        
        self.path_data = path_data
        self.path_reports_folder = self.path_data / "reports"
        self.path_reports_accumulated_folder = self.path_reports_folder / "accumulated"
        self.path_reports_per_day_folder = self.path_reports_folder / "per_day"
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

    def get_trends_accumulated(
            self,
            n_days_back: int = 7,
            date_to: datetime = "now",
            with_save: bool = True) -> pd.DataFrame:
        dfs_range = []
        for date in iter_dates_delta_n_days_back(n_days_back=n_days_back, date_now=date_to):
            trends_date = self.coll.trends_from_date_range(date)
            if trends_date is not None:
                dfs_range.append(trends_date.get_df())

        dfs_range = pd.concat(dfs_range)
        dfs_range = dfs_range.groupby(["name", "query", "url", "domainContext"], as_index=False)["volume"].sum()
        dfs_range.sort_values(by="volume", ascending=False, inplace=True)
        dfs_range.reset_index(drop=True, inplace=True)
        
        if with_save:
            if date_to == "now":
                date_to = datetime.now().date()
            date_from = date_to - timedelta(days=n_days_back - 1)

            path_accumulated = self.path_reports_accumulated_folder / _get_accumulated_name(date_from, date_to)
            dfs_range.to_csv(path_accumulated)
        return dfs_range


    def load_bots(self) -> BotList:
        return BotList.load_from_json(self.path_acc)

    def requests_and_save(self, req_args: Type[ReqArgs], bot: BotScraper) -> InsertOneResult:
        response, creation_date = bot.get_response(req_args)
        insert_one_result_raw = self.add_raw_data(req_args, response, creation_date)
        return insert_one_result_raw

    def __init_db(self) -> None:
        self.path_data.mkdir(exist_ok=True)
        self.path_reports_folder.mkdir(exist_ok=True)
        self.path_reports_accumulated_folder.mkdir(exist_ok=True)
        self.path_reports_per_day_folder.mkdir(exist_ok=True)
        self.path_backup_db.mkdir(exist_ok=True)
    
