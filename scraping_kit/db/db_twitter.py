from __future__ import annotations
from typing import Type, Dict, List, Tuple, Generator, Optional, Iterable
from datetime import datetime, timezone
from pathlib import Path
from requests import Response, JSONDecodeError
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
from bson import ObjectId
from pymongo.results import InsertOneResult
from pymongo.database import Database
from pymongo.collection import Collection

from scraping_kit.db.models.user_full import UserFullData, UsersFullData, TopicUser
from scraping_kit.db.filters import filter_profile, filter_tweet_user, filter_follow
from scraping_kit.dl import instance_classifier
from scraping_kit.utils import iter_dates_by_range, date_one_day, date_delta, format_date_yyyy_mm_dd, format_yyyy_mm_dd
from scraping_kit.db.leak import get_trend_names_uniques
from scraping_kit.db.base import DBMongoBase, HOST_DEFAULT
from scraping_kit.bot_scraper import BotScraper, ReqArgs, BotList
from scraping_kit.db.models.raw import RawData
from scraping_kit.db.models.follow import Follow, FollowList
from scraping_kit.db.models.cursor import Cursor
from scraping_kit.db.models.users import User, UserSuspended, UserList
from scraping_kit.db.models.trends import Trends
from scraping_kit.db.models.search import Search, Tweet
from scraping_kit.db.models.topics import Topic, get_topic_classes
from scraping_kit.db.models.tweet_user import TweetUser
from twitter45.params import ArgsSearch, ArgsUserTimeline, ArgsCheckFollow

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

def iter_args_usertimeline(list_screennames: List[str]) -> ArgsUserTimeline:
    for screenname in list_screennames:
        yield ArgsUserTimeline.from_screenname(screenname, cursor="")

def get_user_timeline(
        bot: BotScraper,
        req_args: ArgsUserTimeline
    ) -> Tuple[Response, datetime, ArgsUserTimeline]:
    response, creation_date = bot.get_response(req_args=req_args)
    return response, creation_date, req_args

def wrap_get_user_timeline(
        db_tw: DBTwitter,
        bot: BotScraper,
        req_args: ArgsUserTimeline,
        days_update=14
    ) -> Tuple[Optional[Response], Optional[datetime], ArgsUserTimeline]:
    _filter = filter_profile(req_args.screenname)
    cursor_doc = db_tw.coll.cursors.find_one(_filter)
    user_suspended = db_tw.coll.user_suspended.find_one(_filter)
    
    if user_suspended is not None:
        return None, None, req_args
    elif cursor_doc is None:
        return get_user_timeline(bot, req_args)
    else:
        cursor = Cursor(**cursor_doc)
        dt = datetime.now() - cursor.creation_date
        if abs(dt.days) >= days_update:
            return get_user_timeline(bot, req_args)
        else:
            return None, None, req_args

def get_check_follow(
        bot: BotScraper,
        req_args: ArgsCheckFollow
    ) -> Tuple[Response, datetime, ArgsCheckFollow]:
    response, creation_date = bot.get_response(req_args=req_args)
    return response, creation_date, req_args

def wrap_check_follow(
        db_tw: DBTwitter,
        bot: BotScraper,
        source: str,
        target: str,
        days_to_update: int = 45
    ) -> bool:
    """ True if `source` follow `target`."""
    req_args = ArgsCheckFollow.from_profiles(source, target)
    _filter_follow = filter_follow(req_args.source, req_args.target)
    follow_doc = db_tw.coll.follows.find_one(_filter_follow)
    
    is_download = False
    if follow_doc is None:
        response, creation_date, req_args = get_check_follow(bot, req_args)
        db_tw.process_check_follow(response, creation_date, req_args)
        is_download = True
    else:
        follow = Follow(**follow_doc)
        dt = datetime.now() - follow.creation_date
        if abs(dt.days) > days_to_update:
            response, creation_date, req_args = get_check_follow(bot, req_args)
            db_tw.process_check_follow(response, creation_date, req_args)
            is_download = True
    return is_download


class DBTwitterColl:
    def __init__(self, db: Database):
        self.cache: Collection = db.get_collection("cache")
        self.raw: Collection = db.get_collection("raw")
        self.trends: Collection = db.get_collection("trends")
        self.topics: Collection = db.get_collection("topics")
        self.topics_user: Collection = db.get_collection("topics_user")
        self.user: Collection = db.get_collection("user")
        self.user_suspended: Collection = db.get_collection("user_suspended")
        self.tweet: Collection = db.get_collection("tweet")     # Este es el tweet del Search.
        self.tweet_user: Collection = db.get_collection("tweet_user")
        self.cursors: Collection = db.get_collection("cursors")
        self.search: Collection = db.get_collection("search")
        self.follows: Collection = db.get_collection("follows")

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
        def clean_invalid_timeline(search_json: dict) -> List[dict]:
            timeline = []
            for t in search_json["timeline"]:
                try:
                    t = Tweet(**t)
                    timeline.append(t.model_dump())
                except:
                    pass
            return timeline
        
        failed_requests = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            iter_futures = (pool.submit(get_tweets_search, random.choice(bots), req_args)
                            for req_args in iter_args_search(trend_names_uniques))
            
            len_trend_names = len(trend_names_uniques)
            for idx, future in enumerate(as_completed(iter_futures), 1):
                search = future.result()
                response, creation_date, req_args = search
                if response.status_code != 200:
                    failed_requests.append(req_args)
                else:
                    search_json = response.json()
                    timeline = clean_invalid_timeline(search_json)

                    i = 1
                    max_tries = 3
                    while (len(timeline) == 0) and (i <= max_tries):
                        print(f"Fail collect - Attempt: 1 | query={req_args.params.query}")
                        search = get_tweets_search(bots.random_bot_2(), req_args)
                        response, creation_date, req_args = search
                        if response.status_code != 200:
                            i += 1
                            continue
                        search_json = response.json()
                        timeline = clean_invalid_timeline(search_json)
                        i += 1
                    
                    search_json["timeline"] = timeline
                    search_json["query"] = req_args.params.query
                    search_json["creation_date"] = creation_date
                    self.search.insert_one(search_json)
                print(f"{idx}/{len_trend_names} - query={req_args.params.query}")
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
        self.path_graph_follow_folder = self.path_reports_folder / "graph_follows"
        self.path_backup_db = self.path_data / "backup_db"
        self.path_blacklist_words = self.path_data / "blacklist_words.xlsx"
        self.path_acc = self.path_data / "acc.json"
        self.path_topic_classes = path_data / "CLASSES_TWITTER.json"
        self.__init_db()
    
    def __init_db(self) -> None:
        self.path_data.mkdir(exist_ok=True)
        self.path_reports_folder.mkdir(exist_ok=True)
        self.path_reports_accumulated_folder.mkdir(exist_ok=True)
        self.path_reports_per_day_folder.mkdir(exist_ok=True)
        self.path_graph_follow_folder.mkdir(exist_ok=True)
        self.path_backup_db.mkdir(exist_ok=True)

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
            with_save: bool = True
        ) -> pd.DataFrame | None:
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
        
        if len(df_accumulated) == 0:
            print("~~~~~ No Data in date range. ~~~~~")
            return None     # Si esta vacío retorna.
        elif len(dates_empty) != 0:
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

    def create_topics_trends(
            self,
            trend_names: List[str],
            topics_1_to_topics_2: dict,
            topics_1: List[str],
            n_text_context: int = 10,
            nro_process: int = None) -> None:
        len_trends = len(trend_names)

        classifier = instance_classifier()
        for i, trend_name in enumerate(trend_names, 1):
            search = Search(**self.coll.search.find_one({"query": trend_name}))
            topic, texts_joined = Topic.create_from_search(search, classifier, topics_1, n_text_context)
            topic.calc_topics_2(topics_1_to_topics_2, texts_joined, classifier, n_text_context)
            self.coll.save_topic(topic)
            
            print(" | ".join([
                f"process {nro_process}",
                f"{i}/{len_trends}",
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
    
    def add_update_tweet_user(self, tweet_user: TweetUser) -> None:
        _filter = filter_tweet_user(tweet_user.tweet_id)
        tweet_user_in_db = self.coll.tweet_user.find_one(_filter)
        if tweet_user_in_db is None:
            self.coll.tweet_user.insert_one(tweet_user.model_dump())
        else:
            self.coll.tweet_user.update_one(_filter, {"$set": tweet_user.model_dump()})
    
    def add_update_user(self, user: User | UserSuspended) -> None:
        _filter = filter_profile(user.profile)
        if isinstance(user, UserSuspended):
            user_in_db = self.coll.user_suspended.find_one(_filter)
            if user_in_db is None:
                self.coll.user_suspended.insert_one(user.model_dump())
        elif isinstance(user, User):
            user_in_db = self.coll.user.find_one(_filter)
            if user_in_db is None:  # Si no existe lo agrega.
                self.coll.user.insert_one(user.model_dump())
            else:                   # Si existe lo actualiza.
                self.coll.user.update_one(_filter, {"$set": user.model_dump()})
        else:
            raise Exception("Invalid user.")
    
    def add_update_cursor(self, cursor: Cursor, user: User | UserSuspended) -> None:
        _filter = filter_profile(user.profile)
        cursor_in_db = self.coll.cursors.find_one(_filter)
        if cursor_in_db is None:
            self.coll.cursors.insert_one(cursor.model_dump())
        else:
            self.coll.cursors.update_one(_filter, {"$set": cursor.model_dump()})

    def find_user(self, profile: str, with_suspended=True) -> User | UserSuspended | None:
        _filter = filter_profile(profile=profile)
        if with_suspended:
            user_suspended_doc = self.coll.user_suspended.find_one(_filter)
            if user_suspended_doc is not None:
                return UserSuspended(**user_suspended_doc)
        
        user_doc = self.coll.user.find_one(_filter)
        if user_doc is not None:
            return User(**user_doc)
        
        return None

    def find_users(self, profiles: List[str], with_suspended=False) -> List[User]:
        users = []
        for profile in profiles:
            user = self.find_user(profile, with_suspended)
            if user is not None:
                users.append(user)
        return users

    def iter_tweet_user(self, profile: str) -> Generator[TweetUser, None, None]:
        for t_doc in self.coll.tweet_user.find({"profile": profile}):
            yield TweetUser(**t_doc)

    def process_user_timeline_response(
            self,
            response: Response,
            creation_date: datetime,
            req_args: ArgsUserTimeline
        ) -> None:
        if response.status_code != 200:
            user = UserSuspended(profile=req_args.screenname)
            self.add_update_user(user)
            return None
        else:
            try:
                data = response.json()
                _user_raw = data.pop("user")
                _status = _user_raw["status"]
                if _status == "suspended" or _status == "error":
                    user = UserSuspended(profile=req_args.screenname)
                    self.add_update_user(user)
                    return None
            except JSONDecodeError:
                user = UserSuspended(profile=req_args.screenname)
                self.add_update_user(user)
                return None
            
            user = User(**_user_raw)
            self.add_update_user(user)
            timeline = data.pop("timeline")
            for tweet_user_doc in timeline:
                if tweet_user_doc["tweet_id"] is not None:
                    tweet_user = TweetUser(
                        rest_id = user.rest_id,
                        profile = user.profile,
                        **tweet_user_doc
                    )
                    self.add_update_tweet_user(tweet_user)
            
            cursor: Optional[str] = Cursor(
                status = user.status,
                profile = user.profile,
                next_cursor = data.pop("next_cursor"),
                creation_date = creation_date
            )
            self.add_update_cursor(cursor, user)

    def collect_usertimeline(self, list_screennames: List[str], bots: BotList, max_workers: int, days_to_update=14) -> list:
        print("~~~~~Start Scraping Users~~~~~")
        list_screennames_leaked = []
        for screenname in list_screennames:
            _user_suspended = self.coll.user_suspended.find_one(filter_profile(screenname))
            if _user_suspended is None:
                list_screennames_leaked.append(screenname)
        len_list_screennames = len(list_screennames_leaked)

        response_errors = []
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            iter_futures = (pool.submit(wrap_get_user_timeline, self, random.choice(bots), req_args, days_to_update)
                            for req_args in iter_args_usertimeline(list_screennames_leaked))
            i = 0
            for future in as_completed(iter_futures):
                user_timeline = future.result()
                if user_timeline[0] is not None:
                    response, creation_date, req_args = user_timeline
                    try:
                        self.process_user_timeline_response(response, creation_date, req_args)
                        i += 1
                        print(f"{i}/{len_list_screennames}")
                    except Exception as e:
                        print(str(e))
                        print(f"{i} error | screenname: {req_args.params.screenname}")
                        response_errors.append((response, creation_date, req_args))
                else:
                    i += 1
            print(f"Completed: {len_list_screennames}/{len_list_screennames}")
        return response_errors
    
    def get_user_full_data(self, profile: str, date_i: datetime, date_f: datetime) -> UserFullData | None:
        _filter = filter_profile(profile=profile)
        user = self.coll.user.find_one(_filter)
        if user is not None:
            user = User(**user)
            tweets_user = []
            for tweet_user_doc in self.coll.tweet_user.find(_filter):
                tweet_user = TweetUser(**tweet_user_doc)
                # FIXME: Ver que hacer en caso que no encuentre nada.
                if date_i <= tweet_user.create_at_datetime and tweet_user.create_at_datetime <= date_f:
                    tweets_user.append(tweet_user)
            topics_user = self.get_topic_user(user)
            return UserFullData(
                user = user,
                tweets_user = tweets_user,
                topics_user = topics_user
            )
        else:
            return None

    def get_bests_users_full_data(
            self,
            profiles: Iterable[str],
            date_i: datetime,
            date_f: datetime,
            n_bests: int
        ) -> UsersFullData:
        users = self.get_user_list(profiles)
        users.keep_bests(n_bests)
        users = self.get_users_full_data(
            profiles = users.iter_profiles(),
            date_i = date_i,
            date_f = date_f
        )
        return users

    def get_users_full_data(
            self,
            profiles: Iterable[str],
            date_i: datetime,
            date_f: datetime
        ) -> UsersFullData:
        all_users = []
        for profile in profiles:
            user_full_data = self.get_user_full_data(profile, date_i, date_f)
            if user_full_data is not None:
                all_users.append(user_full_data)
        return UsersFullData(all_users=all_users)

    def get_user_list(self, list_profiles: List[str]) -> UserList:
        users = self.find_users(list_profiles)
        return UserList(users=users)

    def get_cursor_by_user(self, user: User) -> Cursor:
        _filter = filter_profile(user.profile)
        return Cursor(**self.coll.cursors.find_one(_filter))

    def process_check_follow(
            self,
            response: Response,
            creation_date: datetime,
            req_args: ArgsCheckFollow
        ) -> None:
        
        if response.status_code == 200:
            is_follow = response.json()["is_follow"]

            follow = Follow(
                source = req_args.source,
                target = req_args.target,
                is_follow = is_follow,
                creation_date = creation_date
            )
            
            _filter_follow = filter_follow(req_args.source, req_args.target)
            follow_doc = self.coll.follows.find_one(_filter_follow)
            if follow_doc is None:
                self.coll.follows.insert_one(follow.model_dump())
            else:
                self.coll.follows.update_one(_filter_follow, {"$set": follow.model_dump()})
        else:
            raise Exception(f"Bad requests | source:{req_args.source} | target:{req_args.target}")

    def get_follow_list(self, users: UserList | UsersFullData) -> FollowList:
        if isinstance(users, UserList):
            users_profile = {user.profile: None for user in users}
        elif isinstance(users, UsersFullData):
            users_profile = {user.profile: None for user in users.all_users}

        follows = FollowList(follows=[])
        for follow_doc in self.coll.follows.find({"is_follow": True}):
            follow = Follow(**follow_doc)
            if (follow.source in users_profile) or (follow.target in users_profile):
                follows.append(follow)
        return follows

    def collect_follows(
            self,
            users_full_data: UsersFullData,
            bots: BotList,
            days_to_update_follow_link: int = 120,
            max_workers: int = 40
        ):
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            iter_futures = (pool.submit(wrap_check_follow, self, bots.random_bot_2(), source, target, days_to_update_follow_link)
                            for source, target in users_full_data.iter_profile_pairs())
            n = len(users_full_data)
            num_iters = n * (n - 1)
            for i, future in enumerate(as_completed(iter_futures), 1):
                is_download = future.result()
                txt_iter = f"{i}/{num_iters}"
                if is_download:
                    txt_iter += " | Download sucessfull."
                else:
                    txt_iter += " | Existing link - Skip."
                print(txt_iter)

    def get_topic_user(self, user: User | UserFullData) -> TopicUser:
        topics_user_doc = self.coll.topics_user.find_one({"profile": user.profile})
        if topics_user_doc is not None:
            topic_user = TopicUser(**topics_user_doc)
        else:
            topic_user = TopicUser(profile=user.profile, creation_date=datetime.now())
            self.coll.topics_user.insert_one(topic_user.model_dump())
        return topic_user

    def collect_and_get_users(
            self,
            profiles: List[str],
            bots: BotList,
            date_i: datetime,
            date_f: datetime,
            n_bests_users: int = 30,
            days_to_update_tweets: int = 14,
            days_to_update_follow_link: int = 120,
            with_update: bool = False,
            max_workers: int = 40,
        ) -> UsersFullData:
        assert date_i < date_f, "The end date must be greater."

        if with_update:         # Collect the user's latest tweets.
            self.collect_usertimeline(
                profiles,
                bots = bots,
                max_workers = max_workers,
                days_to_update = days_to_update_tweets
            )
        else:
            print("Users were not updated, set `with_update=True`.")
        
        users = self.get_bests_users_full_data(
            profiles = profiles,
            date_i = date_i,
            date_f = date_f,
            n_bests = n_bests_users
        )
        
        if with_update:         # Collect the links between the chosen users.
            self.collect_follows(
                users,
                bots,
                days_to_update_follow_link,
                max_workers
            )
        else:
            print("Follows were not updated, set `with_update=True`.")
        
        return users

    def collect_trends_today(self, bots: BotList, woeid: str = None, max_workers=10) -> None:
        from twitter_trends.functional import requests_and_process
        requests_and_process(self, bots.random_bot_2(), woeid)   # FIXME: Esta función tendría que ser un método.
        failed_requests = self.collect_searchs_topics(bots, max_workers)
