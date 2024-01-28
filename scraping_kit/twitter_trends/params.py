""" https://rapidapi.com/brkygt88/api/twitter-trends5/"""
from __future__ import annotations
from typing import Type
from pydantic import BaseModel, Field

from scraping_kit import ReqArgs
from scraping_kit.twitter_trends.headers import HeaderTwitterTrends
from scraping_kit.twitter_trends.woeid import WOEIDCountry


class ParamsTwitterTrends(BaseModel):
    woeid: str = Field(default=WOEIDCountry.united_states) # Default: EEUU


class ArgsTwitterTrends(ReqArgs):
    method: str = "POST"
    data: ParamsTwitterTrends = Field(default_factory=ParamsTwitterTrends)

    @classmethod
    def header_cls(cls) -> Type[HeaderTwitterTrends]:
        return HeaderTwitterTrends

    @classmethod
    def endpoint_name(cls) -> str:
        return "trends"

    @classmethod
    def url(cls) -> str:
        return "https://twitter-trends5.p.rapidapi.com/twitter/request.php"

    @classmethod
    def from_woeid(cls, woeid: str = None) -> ArgsTwitterTrends:
        if woeid is None:
            woeid = WOEIDCountry.united_states
        return ArgsTwitterTrends(data=ParamsTwitterTrends(woeid=woeid))