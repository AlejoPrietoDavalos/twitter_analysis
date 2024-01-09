from typing import List, Literal
from datetime import datetime

from pydantic import BaseModel


class UserInfo(BaseModel):
    screen_name: str
    name: str
    followers_count: int
    favourites_count: int
    avatar: str
    verified: bool
    friends_count: int


class Tweet(BaseModel):
    type: Literal["tweet"]
    tweet_id: str
    screen_name: str
    bookmarks: int
    favorites: int
    created_at: str
    text: str
    lang: str
    quotes: int
    replies: int
    retweets: int
    views: str
    user_info: UserInfo
    media: list


class Search(BaseModel):
    timeline: List[Tweet]
    next_cursor: str
    creation_date: datetime


