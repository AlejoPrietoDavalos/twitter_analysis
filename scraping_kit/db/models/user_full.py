from __future__ import annotations
from typing import List, Generator, Tuple
from datetime import datetime

from pydantic import BaseModel
import pandas as pd

from scraping_kit.db.models.users import User
from scraping_kit.db.models.tweet_user import TweetUser
from scraping_kit.const import TopicsNames
from scraping_kit.utils_topics import get_labels_scores

class TopicUserClasses(BaseModel):
    labels: List[str]
    scores: List[float]

    @classmethod
    def from_texts(
        cls,
        texts: List[str],
        classifier,
        classes: List[str]
    ) -> TopicUserClasses:
        labels, scores = get_labels_scores(texts, classifier, classes)
        return TopicUserClasses(labels=labels, scores=scores)


class TopicUser(BaseModel):
    profile: str
    topics_1: TopicUserClasses | None = None
    topics_2: TopicUserClasses | None = None
    creation_date: datetime




class UserFullData(BaseModel):
    user: User
    tweets_user: List[TweetUser]
    topics_user: TopicUser

    def sort_tweets(self, reverse=True) -> None:
        self.tweets_user.sort(key=lambda t: t.create_at_datetime, reverse=reverse)
    
    def iter_tweets(self) -> Generator[TweetUser, None, None]:
        return (tweet_user for tweet_user in self.tweets_user)

    def get_texts(self) -> List[str]:
        self.sort_tweets()
        return [tweet_user.text for tweet_user in self.iter_tweets()]

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

    def iter_profile_pairs(self) -> Generator[Tuple[str, str], None, None]:
        for i, user_i in enumerate(self.all_users):
            for j, user_j in enumerate(self.all_users):
                if i != j:
                    yield user_i.profile, user_j.profile
    
    def df_topics_users(self) -> pd.DataFrame:
        data = {k: [] for k in ["profile",
                                TopicsNames.TOPIC_1_A, TopicsNames.TOPIC_1_B,
                                TopicsNames.TOPIC_2_A, TopicsNames.TOPIC_2_B]}
        for user in self.all_users:
            data["profile"].append(user.profile)
            t1 = user.topics_user.topics_1
            t2 = user.topics_user.topics_2
            if t1 is not None:
                topic_1_a, topic_1_b = t1.labels[:2]
            else:
                topic_1_a, topic_1_b = "", ""
            if t2 is not None:
                topic_2_a, topic_2_b = t2.labels[:2]
            else:
                topic_2_a, topic_2_b = "", ""
            data[TopicsNames.TOPIC_1_A].append(topic_1_a)
            data[TopicsNames.TOPIC_1_B].append(topic_1_b)
            data[TopicsNames.TOPIC_2_A].append(topic_2_a)
            data[TopicsNames.TOPIC_2_B].append(topic_2_b)
        df = pd.DataFrame(data)
        return df