from __future__ import annotations
from typing import Type, TypeVar, Tuple
from pydantic import BaseModel
from abc import abstractclassmethod
from datetime import datetime
from requests import Response

from scraping_kit.bot_scraper import BotScraper, ReqArgs


T_BaseDBModel = TypeVar("T_BaseDBModel", bound="BaseDBModel")

class BaseDBModel(BaseModel):
    @abstractclassmethod
    def from_request(
            cls: Type[T_BaseDBModel],
            req_args: Type[ReqArgs],
            bot: BotScraper
        ) -> T_BaseDBModel:
        """ Make the request and return the processed object."""
        response, creation_date = bot.get_response(req_args=req_args)
        return response, creation_date

