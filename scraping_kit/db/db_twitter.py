from pathlib import Path

from pymongo.database import Database
from pymongo.collection import Collection

from _twitter154.db.base import DBMongoBase, HOST_DEFAULT


class DBTwitterColl:
    def __init__(self, db: Database):
        self.__raw: Collection = db["raw"]
        self.__user: Collection = db["user"]
        self.__user_suspended: Collection = db["user_suspended"]
        self.__tweet: Collection = db["tweet"]
        self.__cursors: Collection = db["cursors"]

    @property
    def raw(self) -> Collection:
        return self.__raw

    @property
    def user(self) -> Collection:
        return self.__user
    
    @property
    def user_suspended(self) -> Collection:
        return self.__user_suspended

    @property
    def tweet(self) -> Collection:
        return self.__tweet
    
    @property
    def cursors(self) -> Collection:
        return self.__cursors


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
        


