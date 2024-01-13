from __future__ import annotations
from pathlib import Path
import json
from typing import List, Tuple, Optional, Literal
from datetime import datetime

from pydantic import BaseModel
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from transformers.pipelines.zero_shot_classification import ZeroShotClassificationPipeline

from scraping_kit.db.models.search import Search


def get_topic_classes(path_topic_classes: Path) -> Tuple[dict, list]:
    with open(path_topic_classes, "r") as f:
        topics_1_to_topics_2: dict = json.load(f)
        topics_1 = list(topics_1_to_topics_2.keys())
    return topics_1_to_topics_2, topics_1


class TopicClasses(BaseModel):
    labels: List[str]
    scores: List[float]
    n_first_texts: int


class Topic(BaseModel):
    query: str
    topics_1: TopicClasses
    topics_2: TopicClasses | None = None
    creation_date: datetime

    @classmethod
    def create_from_search(
            cls,
            search: Search,
            classifier: ZeroShotClassificationPipeline,
            classes: List[str],
            n_first_texts: int = 5,
            multi_label: bool = False
        ) -> Tuple[Topic, str]:
        texts_joined = "\n".join(search.get_texts()[:n_first_texts])
        topic_classes = classifier(texts_joined, candidate_labels=classes, multi_label=multi_label)
        topic_classes["n_first_texts"] = n_first_texts
        topic_classes.pop("sequence")
        topic = Topic(
            query = search.query,
            topics_1 = topic_classes,
            creation_date = search.creation_date
        )
        return topic, texts_joined
    
    def calc_topics_2(
            self,
            topics_1_to_topics_2: dict,
            texts_joined: str,
            classifier: ZeroShotClassificationPipeline,
            n_text_context: int = 5,
            multi_label: bool = False
        ) -> None:
        topics_1_a, topics_1_b = self.topics_1.labels[:2]
        classes = topics_1_to_topics_2[topics_1_a] + topics_1_to_topics_2[topics_1_b]
        topic_classes = classifier(texts_joined, candidate_labels=classes, multi_label=multi_label)
        topic_classes["n_first_texts"] = n_text_context
        topic_classes.pop("sequence")
        self.topics_2 = TopicClasses(**topic_classes)

    def idx_threshold(
            self,
            threshold: float,
            what_topics: Literal["topics_1", "topics_2"] = "topics_1"
        ) -> int:
        if what_topics == "topics_1":
            len_topics = len(self.topics_1.scores)
        elif what_topics == "topics_2":
            len_topics = len(self.topics_2.scores)
        else:
            raise Exception("Tipo de topics incorrecto")
        
        i, flag = 0, True
        while flag and i<len_topics:
            if what_topics == "topics_1":
                score = self.topics_1.scores[i]
            elif what_topics == "topics_2":
                score = self.topics_2.scores[i]
            else:
                raise Exception("Tipo de topics incorrecto")
            if score <= threshold:
                flag = False
            else:
                i += 1
        return i

    def get_labels_scores_thresh(
            self,
            threshold: float,
            what_topics: Literal["topics_1", "topics_2"] = "topics_1"
        ) -> Tuple[List[str], List[float]]:
        i = self.idx_threshold(threshold)
        if what_topics == "topics_1":
            labels = self.topics_1.labels[:i]
            score = self.topics_1.scores[:i]
        elif what_topics == "topics_2":
            labels = self.topics_2.labels[:i]
            score = self.topics_2.scores[:i]
        else:
            raise Exception("Tipo de topics incorrecto")
        return labels, score

    def plot(self, threshold: float) -> Axes:
        fig, ax = plt.subplots(dpi=150)
        ax.bar(self.get_labels_scores_thresh(threshold))
        ax.set_title(f"trend_name: {self.query}")
        return ax