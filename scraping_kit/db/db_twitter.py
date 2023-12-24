from typing import List
from pathlib import Path

from pymongo.database import Database
from pymongo.collection import Collection

from scraping_kit.db.base import DBMongoBase, HOST_DEFAULT
from scraping_kit.bot_scraper import load_bots, BotScraper


class DBTwitterColl:
    def __init__(self, db: Database):
        self.raw: Collection = db.get_collection("raw")
        self.user: Collection = db.get_collection("user")
        self.user_suspended: Collection = db.get_collection("user_suspended")
        self.tweet: Collection = db.get_collection("tweet")
        self.cursors: Collection = db.get_collection("cursors")


class DBTwitter(DBMongoBase):
    def __init__(self, path_data: Path, db_name: str, host=HOST_DEFAULT):
        super().__init__(db_name=db_name, host=host)
        self.coll = DBTwitterColl(db = self.db)
        
        self.path_data = path_data
        self.path_reports_folder = self.path_data / "reports"
        self.path_acc = self.path_data / "acc.json"
        self.__init_db()
    
    def load_bots(self) -> List[BotScraper]:
        return BotScraper.load_bots(self.path_acc)

    def __init_db(self) -> None:
        self.path_data.mkdir(exist_ok=True)
        self.path_reports_folder.mkdir(exist_ok=True)

