from typing import List

from pymongo.database import Database
from pymongo.collection import Collection

from twitter154.db.base import DBMongoBase, HOST_DEFAULT


class DBTwitterColl:
    def __init__(self, db: Database):
        self.__user: Collection = db["user"]
        self.__tweet: Collection = db["tweet"]
        self.__tweets_continuation: Collection = db["tweets_continuation"]

    @property
    def user(self) -> Collection:
        return self.__user
    
    @property
    def tweet(self) -> Collection:
        return self.__tweet
    
    @property
    def tweets_continuation(self) -> Collection:
        return self.__tweets_continuation


class DBTwitter(DBMongoBase):
    def __init__(self, db_name: str, host=HOST_DEFAULT):
        super().__init__(db_name=db_name, host=host)
        self.__coll = DBTwitterColl(db = self.db)

    @property
    def coll(self) -> DBTwitterColl:
        return self.__coll


