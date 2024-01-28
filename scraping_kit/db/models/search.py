from typing import List, Literal, Optional, Generator
from functools import cached_property
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
    views: Optional[int]
    user_info: UserInfo
    media: dict | list

    @cached_property
    def create_at_datetime(self) -> datetime:
        return datetime.strptime(self.created_at, '%a %b %d %H:%M:%S %z %Y')


class Search(BaseModel):
    query: str
    timeline: List[Tweet]
    next_cursor: Optional[str]
    creation_date: datetime

    def __getitem__(self, idx: int) -> Tweet:
        return self.timeline[idx]

    def iter_tweets(self) -> Generator[Tweet, None, None]:
        return (tweet for tweet in self.timeline)

    def sort_tweets(self):
        def _sort_metric(t: Tweet) -> int:
            views = 0 if t.views is None else t.views
            return t.replies + t.retweets + t.favorites + views
        self.timeline.sort(key=_sort_metric, reverse=True)

    def get_texts(self) -> List[str]:
        self.sort_tweets()
        return [tweet.text for tweet in self.iter_tweets()]
