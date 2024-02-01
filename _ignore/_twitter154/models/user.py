from datetime import datetime

from _twitter154.models.common import ValCommonModel

USER_ID = "user_id"
USERNAME = "username"

class User(ValCommonModel):
    creation_date: datetime
    user_id: str
    username: str
    name: str
    follower_count: int
    following_count: int
    favourites_count: int
    is_private: bool
    is_verified: bool
    is_blue_verified: bool
    location: str
    profile_pic_url: str
    profile_banner_url: str
    description: str
    external_url: str | None
    number_of_tweets: int
    bot: bool
    timestamp: int
    has_nft_avatar: bool
    category: list | None
    default_profile: bool
    default_profile_image: bool
    listed_count: int
    verified_type: str | None