from abc import ABC

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection


class DBMongoBase(ABC):
    def __init__(self, db_name: str, host="mongodb://localhost:27017/"):
        self.__client = MongoClient(host)
        self.__db: Database = self.__client[db_name]
    
    @property
    def client(self) -> MongoClient:
        return self.__client

    @property
    def db(self) -> Database:
        return self.__db

    def __getitem__(self, key: str) -> Collection:
        """ Retorna la colección."""
        return self.db[key]


class DBTwitter(DBMongoBase):
    pass
#    @property


