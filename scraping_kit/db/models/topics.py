from typing import List, Tuple
from datetime import datetime

from pydantic import BaseModel
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


class TopicClasses(BaseModel):
    text: str
    labels: List[str]
    scores: List[float]


class Topic(BaseModel):
    trend_name: str
    topic_classes: TopicClasses
    creation_date: datetime

    def idx_threshold(self, threshold: float) -> int:
        i, flag = 0, True
        while flag and i<len(self.topic_classes.scores):
            if self.topic_classes.scores[i] <= threshold:
                flag = False
            else:
                i += 1
        return i

    def get_labels_scores_thresh(self, threshold: float) -> Tuple[List[str], List[float]]:
        i = self.idx_threshold(threshold)
        return self.topic_classes.labels[:i], self.topic_classes.scores[:i]

    def plot(self, threshold: float) -> Axes:
        fig, ax = plt.subplots(dpi=150)
        ax.bar(self.get_labels_scores_thresh(threshold))
        ax.set_title(f"trend_name: {self.trend_name}")
        return ax