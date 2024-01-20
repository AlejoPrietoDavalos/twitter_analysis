from typing import List, Generator

from pydantic import BaseModel

from scraping_kit.db.models.users import User
from scraping_kit.db.models.tweet_user import TweetUser

class UserFullData(BaseModel):
    user: User
    tweets_user: List[TweetUser]

    def sort_tweets(self, reverse=True) -> None:
        self.tweets_user.sort(key=lambda t: t.create_at_datetime, reverse=reverse)
    
    def iter_tweets(self) -> Generator[TweetUser, None, None]:
        return (tweet_user for tweet_user in self.tweets_user)

    def get_texts(self, n_first_texts: int = None) -> List[str]:
        """ TODO: Considerar otros textos, likes etc..."""
        self.sort_tweets()
        texts = [tweet_user.text for tweet_user in self.iter_tweets()]
        return texts if n_first_texts is None else texts[:n_first_texts]

    @property
    def profile(self) -> str:
        return self.user.profile

    @property
    def following(self) -> int:
        return self.user.following

    @property
    def followers(self) -> int:
        return self.user.followers


class UsersFullData(BaseModel):
    all_users: List[UserFullData]

    def __getitem__(self, idx: int) -> UserFullData:
        return self.all_users[idx]
    
    def __len__(self) -> int:
        return len(self.all_users)

    def sort_all(self, reverse=True) -> None:
        for user in self.all_users:
            user.sort_tweets(reverse=reverse)
