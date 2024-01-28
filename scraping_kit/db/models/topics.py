from __future__ import annotations
from typing import List, Tuple, Optional, Dict
from pathlib import Path
import json
from datetime import datetime

from pydantic import BaseModel
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from scraping_kit.db.models.search import Search


def get_topic_classes(path_topic_classes: Path) -> Tuple[dict, list]:
    with open(path_topic_classes, "r") as f:
        topics_1_to_topics_2: dict = json.load(f)
        topics_1 = list(topics_1_to_topics_2.keys())
    return topics_1_to_topics_2, topics_1


def get_labels_scores(texts: List[str], classifier, classes: List[str]) -> Tuple[List[str], List[float]]:
    labels_score_aux = {label: 0 for label in classes}

    for text in texts:
        pred = classifier(text, candidate_labels=classes)
        pred.pop("sequence")
        for label, score in zip(pred["labels"], pred["scores"]):
            labels_score_aux[label] += score
    label_scores = [(label, score/len(texts)) for label, score in labels_score_aux.items()]

    label_scores.sort(key=lambda l_s: l_s[1], reverse=True)
    labels, scores = zip(*label_scores)
    return labels, scores


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
        classes_2 = [elem for item in topics_1.labels[:2] for elem in classes_1_to_2[item]]
        topics_2 = TopicClasses.from_texts(texts, classifier, classes_2)
        return Topic(
            query = query,
            topics_1 = topics_1,
            topics_2 = topics_2,
            creation_date = creation_date
        )
