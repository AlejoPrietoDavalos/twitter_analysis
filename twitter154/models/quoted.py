from typing import Literal, Any, List

from pydantic import BaseModel

from twitter154.models.user import User
from twitter154.models.common import ValCommonModel

"""
class StringValue(BaseModel):
    string_value: str
    type: Literal["STRING"]

class BindingStringValue(BaseModel):
    string_value: str
    type: Literal["STRING"]

class ImageValue(BaseModel):
    height: int
    width: int
    url: str

class BindingImageValue(BaseModel):
    image_value: ImageValue
    type: Literal["IMAGE"]   # Literal["IMAGE", "STRING"]
"""


T_binding_values_key = Literal[
    "thumbnail_image", "thumbnail_image_small", "thumbnail_image_large", "thumbnail_image_original",
    "thumbnail_image_x_large", "thumbnail_image_alt_text", "thumbnail_image_color", "site", "domain",
    "description", "vanity_url", "title", "card_url"]

class BindingValues(BaseModel):
    key: T_binding_values_key
    value: Any#BindingImageValue | BindingStringValue

class QuotedStatus(ValCommonModel):
    tweet_id: str
    text: str
    media_url: List[str] | None
    video_url: None     # TODO: str? List[str]?
    user: User
    language: str
    favorite_count: int
    retweet_count: int
    reply_count: int
    quote_count: int
    retweet: bool
    views: int
    timestamp: int
    video_view_count: None
    in_reply_to_status_id: None
    quoted_status_id: str | None
    binding_values: Any | None#List[BindingValues] | None
    expanded_url: Any
    retweet_tweet_id: Any
    extended_entities: Any
    conversation_id: Any
    retweet_status: Any
    quoted_status: Any
    bookmark_count: Any
    source: Any