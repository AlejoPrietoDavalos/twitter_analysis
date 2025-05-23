from typing import Generator, List
from datetime import datetime

from pydantic import BaseModel

from _twitter154.models.user import User, USER_ID, USERNAME
from _twitter154.models.common import ValCommonModel
from _twitter154.models.quoted import QuotedStatus
from _twitter154.models.media import ExtendedEntities

class TweetLike(ValCommonModel):
    tweet_id: str
    creation_date: datetime
    text: str
    media_url: List[str] | None
    video_url: None         # TODO: -> Testear. No hay caso de uso.
    user_id: str
    username: str
    ############### user: User
    language: str
    favorite_count: int
    retweet_count: int
    reply_count: int
    quote_count: int
    retweet: bool
    views: int
    timestamp: int
    video_view_count: None
    in_reply_to_status_id: str | None
    quoted_status_id: str | None
    binding_values: None
    expanded_url: str | None
    retweet_tweet_id: str | None
    extended_entities: ExtendedEntities | None
    conversation_id: str
    quoted_status: QuotedStatus | None
    bookmark_count: int
    source: str

    def __init__(self, **data):
        # Extrae el usuario y guarda únicamente sus ID's.
        if "user" in data:
            user = User(**data.pop("user"))
            data[USER_ID] = user.user_id
            data[USERNAME] = user.username
        super().__init__(**data)


class ReTweet(TweetLike):
    retweet_status: None | TweetLike

class Tweet(TweetLike):
    retweet_status: None | TweetLike

class Tweets(BaseModel):
    results: List[Tweet]
    continuation_token: str

    def __len__(self) -> int:
        return len(self.results)

    def __getitem__(self, idx: int) -> Tweet:
        return self.results[idx]

    def iter_tweet(self, reverse=False) -> Generator[Tweet, None, None]:
        if not reverse:
            return (tweet for tweet in reversed(self.results))
        return (tweet for tweet in self.results)

class TweetsContinuation(BaseModel):
    user_id: str
    username: str
    continuation_token: str