from typing import Literal, Optional
from pydantic import BaseModel

class UserSuspended(BaseModel):
    status: Literal["suspended"] = "suspended"
    profile: str


class User(BaseModel):
    status: Literal["active"] = "active"
    profile: str
    rest_id: str
    blue_verified: bool
    avatar: str
    header_image: Optional[str]
    desc: str
    name: str
    protected: Optional[bool]
    location: str
    friends: int
    sub_count: int
    id: str

