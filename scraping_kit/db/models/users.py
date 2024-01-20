from __future__ import annotations
from typing import List, Literal, Optional, Generator, Tuple
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
    sub_count: int          # Este es el que importa.
    id: str

    @property
    def following(self) -> int:
        return self.friends

    @property
    def followers(self) -> int:
        return self.sub_count


class UserList(BaseModel):
    users: List[User]

    def __getitem__(self, idx: int) -> User:
        return self.users[idx]

    def __len__(self) -> int:
        return len(self.users)

    def __iter__(self):
        return iter(self.users)

    def iter_profiles(self) -> Generator[str, None, None]:
        return (user.profile for user in self.users)

    def sort(self, reverse=True) -> None:
        self.users.sort(key=lambda user: user.sub_count, reverse=reverse)
    
    def keep_bests(self, n_bests: int) -> None:
        self.sort()
        self.users = self.users[:n_bests]

    def iter_profile_pairs(self) -> Generator[Tuple[str, str], None, None]:
        for i, user_i in enumerate(self.users):
            for j, user_j in enumerate(self.users):
                if i != j:
                    yield user_i.profile, user_j.profile
    
    def get_profile_pairs(self) -> List[Tuple[str, str]]:
        return list((s, t) for s, t in self.iter_profile_pairs())