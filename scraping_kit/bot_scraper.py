from __future__ import annotations
from typing import Type, List, Tuple, Literal, Generator
from pathlib import Path
import random
import json
import requests
from requests import Response
from datetime import datetime
from abc import ABC, abstractclassmethod, abstractmethod

from pydantic import BaseModel, Field


class Headers(ABC):
    @abstractclassmethod
    def get_header(cls, bot_scraper: BotScraper) -> dict:
        """ It must return the header necessary to send the requests to the API."""
        ...


class ReqArgs(BaseModel, ABC):
    """ It must contain only the elements necessary to make the requests."""
    method: Literal["GET", "POST"] = "GET"

    @abstractclassmethod
    def header_cls(cls) -> Type[Headers]:
        """ Must return the header class."""
        ...

    @abstractclassmethod
    def endpoint_name(cls) -> str:
        """ Endpoint name."""
        ...

    @abstractclassmethod
    def url(cls) -> str:
        """ Endpoint URL."""
        ...
    
    # def process_response(self, response: Response) -> dict:
    #     if 
    #     return {}

    @classmethod
    def get_header(cls, bot_scraper: BotScraper) -> dict:
        header_cls = cls.header_cls()
        return header_cls.get_header(bot_scraper)

    def response_dump(self, bot_scraper: BotScraper) -> dict:
        """ FIXME: Hardcoding."""
        model_dump_ = super().model_dump()
        model_dump_["url"] = self.url()
        model_dump_["headers"] = self.get_header(bot_scraper)
        return model_dump_

    def model_dump(self) -> dict:
        """ FIXME: Hardcoding."""
        model_dump_ = super().model_dump()
        model_dump_["url"] = self.url()
        model_dump_["endpoint_name"] = self.endpoint_name()
        return model_dump_


class BotScraper(BaseModel):
    """ Main object with which requests are made."""
    acc_name: str = Field(frozen=True)
    credential: str = Field(frozen=True, repr=False)
    
    def get_response(self, req_args: Type[ReqArgs]) -> Tuple[Response, datetime]:
        response = requests.request(**req_args.response_dump(self))
        creation_date = datetime.now()
        return response, creation_date


T_BotChoiced = Tuple[int, BotScraper]

class BotList(BaseModel):
    bots: List[BotScraper]

    def __getitem__(self, idx: int) -> BotScraper:
        return self.bots[idx]
    
    def __len__(self) -> int:
        return len(self.bots)

    @classmethod
    def load_from_json(cls, path_acc: Path) -> BotList:
        with open(path_acc, "r") as f:
            bots = [BotScraper(**acc_json) for acc_json in json.load(f)]
        return cls(bots=bots)

    def random_bot(self) -> T_BotChoiced:
        idx = random.randint(0, len(self.bots) - 1)
        return idx, self.bots[idx]

    def iter_random_bot(self, n_iters: int) -> Generator[T_BotChoiced, None, None]:
        return (self.random_bot() for _ in range(n_iters))
