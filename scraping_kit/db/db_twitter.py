from __future__ import annotations
from typing import Type, Dict, List, Tuple, Generator
from datetime import datetime
from pathlib import Path
from requests import Response
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import numpy as np
from bson import ObjectId
from pymongo.results import InsertOneResult
from pymongo.database import Database
from pymongo.collection import Collection

from scraping_kit.dl import instance_classifier
from scraping_kit.db.base import DBMongoBase, HOST_DEFAULT
from scraping_kit.bot_scraper import BotScraper, ReqArgs, BotList
from scraping_kit.db.models.raw import RawData
from scraping_kit.db.models.trends import Trends
from scraping_kit.utils import iter_dates_by_range, date_one_day
from scraping_kit.db.models.search import Search
from scraping_kit.db.models.topics import Topic
from scraping_kit.db.leak import get_trend_names_uniques
from twitter45.params import ArgsSearch


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

def iter_args_search(trend_names: List[str]) -> Generator[ArgsSearch, None, None]:
    return (ArgsSearch.from_trend_name(trend_name) for trend_name in (trend_names))

def get_tweets_search(bot: BotScraper, req_args: ArgsSearch) -> Tuple[Response, datetime, ArgsSearch] | None:
    """ `query_str` must be the 'query' element within the dataframe."""
    response, creation_date = bot.get_response(req_args)
    return response, creation_date, req_args


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

    def collect_searchs_by_trends(
            self,
            trend_names_uniques: List[str],
            bots: BotList,
            max_workers: int = 1
        ) -> List[ArgsSearch]:
        """ Recolecta los searchs para cada trend, y retorna los requests fallidos."""
        failed_requests = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            iter_futures = (pool.submit(get_tweets_search, random.choice(bots), req_args)
                            for req_args in iter_args_search(trend_names_uniques))
            
            for future in as_completed(iter_futures):
                search = future.result()
                response, creation_date, req_args = search
                if response.status_code != 200:
                    failed_requests.append(req_args)
                else:
                    search_json = response.json()
                    search_json["query"] = req_args.params.query
                    search_json["creation_date"] = creation_date
                    self.search.insert_one(search_json)
        
        n_failed = len(failed_requests)
        if n_failed == 0:
            print("--> All downloads were completed without problems.")
        else:
            print(f"--> There were {n_failed} failed downloads, try running this script again after a while.")
        return failed_requests
    
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


        # Se agregan los topics.
        df_accumulated["topics_1_a"] = ""
        df_accumulated["topics_1_b"] = ""
        df_accumulated["topics_2_a"] = ""
        df_accumulated["topics_2_b"] = ""
        for i, row in df_accumulated.iterrows():
            name = row["name"]
            topic_doc = self.coll.topics.find_one({"query": name})
            if topic_doc is not None:
                topic = Topic(**topic_doc)
                #topics_concat = " | ".join(topic.topics_1.labels[:2])  # Obtengo los primeros 2.
                topics_1_a, topics_1_b = topic.topics_1.labels[:2]
                df_accumulated.loc[i, "topics_1_a"] = topics_1_a
                df_accumulated.loc[i, "topics_1_b"] = topics_1_b
                
                topics_2_a, topics_2_b = topic.topics_2.labels[:2]
                df_accumulated.loc[i, "topics_2_a"] = topics_2_a
                df_accumulated.loc[i, "topics_2_b"] = topics_2_b
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

    def create_topics_trends(self, trend_names: List[str], topics_1_to_topics_2: dict, topics_1: List[str], n_text_context=10, nro_process=None):
        len_trends = len(trend_names)
        #dts = []
        classifier = instance_classifier()
        for i, trend_name in enumerate(trend_names, 1):
            #t_i = time.time()
            search = Search(**self.coll.search.find_one({"query": trend_name}))
            topic, texts_joined = Topic.create_from_search(search, classifier, topics_1, n_text_context)
            topic.calc_topics_2(topics_1_to_topics_2, texts_joined, classifier, n_text_context)
            self.coll.save_topic(topic)
            
            #dts.append(time.time() - t_i)
            #n_remaining = len_trends - i
            print(" | ".join([
                f"process {nro_process}",
                f"{i}/{len_trends}",
                #f"time_stimated={int(n_remaining * np.mean(dts)) / 60} min",
                f"trend_name: {topic.query}",
                f"topics_1: {topic.topics_1.labels[:2]}",
                f"topics_2: {topic.topics_2.labels[:2]}"
            ]))

    def collect_searchs_topics(self, bots: BotList, max_workers: int) -> list:
        trend_names_uniques = get_trend_names_uniques(self, not_in_topics=True, not_in_searchs=True)
        failed_requests = self.coll.collect_searchs_by_trends(
            trend_names_uniques,
            bots,
            max_workers
        )
        return failed_requests

    def get_trends_to_create_topics(self) -> List[str]:
        """ Esta función retorna todos los trend_names para hacer los topics."""
        trend_names = []
        for search_doc in self.coll.search.find():
            search = Search(**search_doc)
            topic_doc = self.coll.topics.find_one({"query": search.query})
            if topic_doc is None:
                trend_names.append(search.query)
        return trend_names

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
    
