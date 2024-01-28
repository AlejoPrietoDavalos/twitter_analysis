from typing import Tuple, List
from pathlib import Path
import json

def get_classes_2(topics_1_labels: List[str], classes_1_to_2: dict[str]) -> List[str]:
    return [elem for item in topics_1_labels[:2] for elem in classes_1_to_2[item]]

def get_topic_classes(path_topic_classes: Path) -> Tuple[dict, list]:
    with open(path_topic_classes, "r") as f:
        topics_1_to_topics_2: dict = json.load(f)
        topics_1 = list(topics_1_to_topics_2.keys())
    return topics_1_to_topics_2, topics_1

def get_labels_scores(
        texts: List[str],
        classifier,
        classes: List[str]
    ) -> Tuple[List[str], List[float]]:
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