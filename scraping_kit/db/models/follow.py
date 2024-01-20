from typing import List, Tuple
from datetime import datetime

from pydantic import BaseModel

class Follow(BaseModel):
    source: str
    target: str
    is_follow: bool
    creation_date: datetime

class FollowList(BaseModel):
    follows: List[Follow]

    @property
    def list_of_tuples(self) -> list[Tuple[str, str]]:
        return list((follow.source, follow.target) for follow in self.follows)

    def __getitem__(self, idx: int) -> Follow:
        return self.follows[idx]

    def __len__(self) -> int:
        return len(self.follows)
    
    def __iter__(self):
        return iter(self.follows)
    
    def append(self, follow: Follow) -> None:
        assert isinstance(follow, Follow), "Objeto incorrecto."
        self.follows.append(follow)