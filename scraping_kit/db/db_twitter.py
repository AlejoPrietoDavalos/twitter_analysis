from pathlib import Path

from pymongo.database import Database
from pymongo.collection import Collection

from scraping_kit.db.base import DBMongoBase, HOST_DEFAULT


class DBTwitterColl:
    def __init__(self, db: Database):
        self.raw: Collection = db["raw"]
        self.user: Collection = db["user"]
        self.user_suspended: Collection = db["user_suspended"]
        self.tweet: Collection = db["tweet"]
        self.cursors: Collection = db["cursors"]

class DBTwitter(DBMongoBase):
    def __init__(self, path_data: Path, db_name: str, host=HOST_DEFAULT):
        super().__init__(db_name=db_name, host=host)
        self.__coll = DBTwitterColl(db = self.db)
        self.__init_db(path_data=path_data)
    
    @property
    def coll(self) -> DBTwitterColl:
        return self.__coll
    
    def __init_db(self, path_data: Path) -> None:
        path_data.mkdir(exist_ok=True)
        


