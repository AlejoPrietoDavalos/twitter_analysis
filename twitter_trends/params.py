import requests

from pydantic import BaseModel, Field

from scraping_kit.responser import ReqArgs
from twitter_trends.woeid import WOEIDCountry

class ParamsTwitterTrends(BaseModel):
    woeid: str = Field(default=WOEIDCountry.united_states) # Default: EEUU

class ArgsTwitterTrends(ReqArgs):
    data: ParamsTwitterTrends = Field(default_factory=ParamsTwitterTrends)

    @classmethod
    def endpoint_name(cls) -> str:
        return "trends"

    @classmethod
    def url(cls) -> str:
        return "https://twitter-trends5.p.rapidapi.com/twitter/request.php"
