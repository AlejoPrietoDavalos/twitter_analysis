from __future__ import annotations
from typing import Type, List, Tuple, Literal
from pathlib import Path
import json
import requests
from requests import Response
from datetime import datetime
from abc import ABC, abstractclassmethod

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
    
    @classmethod
    def get_header(cls, bot_scraper: BotScraper) -> dict:
        header_cls = cls.header_cls()
        return header_cls.get_header(bot_scraper)

    def response_dump(self) -> dict:
        """ FIXME: Hardcoding."""
        model_dump_ = super().model_dump()
        model_dump_["url"] = self.url()
        return model_dump_

    def model_dump(self) -> dict:
        """ FIXME: Hardcoding."""
        model_dump_ = self.response_dump()
        model_dump_["endpoint_name"] = self.endpoint_name()
        return model_dump_


class BotScraper(BaseModel):
    """ Main object with which requests are made."""
    acc_name: str = Field(frozen=True)
    credential: str = Field(frozen=True, repr=False)

    @classmethod
    def load_bots(cls, path_acc: Path) -> List[BotScraper]:
        with open(path_acc) as f:
            return [BotScraper(**acc_json) for acc_json in json.load(f)]
    
    def get_response(self, req_args: Type[ReqArgs]) -> Tuple[Response, datetime]:
        response = requests.request(**req_args.response_dump(), headers=req_args.get_header(self))
        date_now = datetime.now()
        return response, date_now

