from __future__ import annotations
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import json
from datetime import datetime

from pydantic import BaseModel

from scraping_kit.utils_topics import get_labels_scores, get_classes_2


class TopicClasses(BaseModel):
    labels: List[str]
    scores: List[float]

    @classmethod
    def from_texts(cls, texts: List[str], classifier, classes: List[str]) -> TopicClasses:
        labels, scores = get_labels_scores(texts, classifier, classes)
        return TopicClasses(labels=labels, scores=scores)



class Topic(BaseModel):
    query: str
    topics_1: Optional[TopicClasses]
    topics_2: Optional[TopicClasses]
    creation_date: datetime

    @classmethod
    def from_texts(
            cls,
            query: str,
            texts: List[str],
            creation_date: datetime,
            classifier,
            classes_1: List[str],
            classes_1_to_2: Dict[List[str]]
        ) -> Topic:
        topics_1 = TopicClasses.from_texts(texts, classifier, classes_1)
        classes_2 = get_classes_2(topics_1.labels, classes_1_to_2)
        topics_2 = TopicClasses.from_texts(texts, classifier, classes_2)
        return Topic(
            query = query,
            topics_1 = topics_1,
            topics_2 = topics_2,
            creation_date = creation_date
        )
