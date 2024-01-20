from typing import List, Any, Optional
from datetime import datetime
from functools import cached_property

from pydantic import BaseModel


#class MediaUrlHTTPS(BaseModel):
#    media_url_https: str

#class MediaTweet(BaseModel):
#    photo: List[MediaUrlHTTPS]

class TweetUser(BaseModel):
    tweet_id: str
    rest_id: str
    profile: str
    bookmarks: int
    created_at: str         #'Tue Jan 09 12:49:26 +0000 2024',
    favorites: int
    text: str
    lang: str               #'en'
    views: Optional[str]
    quotes: int
    replies: int
    retweets: int
    conversation_id: str
    media: Any

    @cached_property
    def create_at_datetime(self) -> datetime:
        return datetime.strptime(self.created_at, '%a %b %d %H:%M:%S %z %Y')

    '''
    def __init__(self, **data):
        author = data.get("author", None)
        if author is not None:
            data.update({
                "rest_id": author.pop("rest_id"),
                "profile": author.pop("screen_name")
            })
        super().__init__(**data)
    '''
