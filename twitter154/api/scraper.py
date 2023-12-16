import requests
from requests import Response
from functools import cached_property

from pydantic import BaseModel

from twitter154.models import Tweets
from twitter154.api.headers import get_headers
from twitter154.api._methods import GET, POST

def url_api() -> str:
    return "https://twitter154.p.rapidapi.com"

def url_user_tweets() -> str:
    return f"{url_api()}/user/tweets"

class TwResponser:
    @staticmethod
    def user_tweets(headers: dict, querystring: dict) -> Response:
        """
        ```python
        querystring = {
            "username": "the_name",
            "limit": "40",
            "user_id": "19283750",
            "include_replies": "false",
            "include_pinned": "false"
        }
        ```
        """
        url = url_user_tweets()
        response: Response = requests.request(GET, url=url, headers=headers, params=querystring)
        return response


class Scraper:
    def __init__(self):
        pass

    @cached_property
    def headers(self) -> dict:
        return get_headers()
    
    def get_user_tweets(self, querystring: dict) -> Tweets:
        response = TwResponser.user_tweets(headers=self.headers, querystring=querystring)
        response_json = response.json()
        try:
            tweets = Tweets(**response_json)
        except:
            # Guardar.
            pass
        return tweets

