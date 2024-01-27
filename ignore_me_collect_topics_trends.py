""" `python3 search_to_topic_subprocess.py n_process`"""
from typing import List, Any
import sys
import multiprocessing
from pathlib import Path

from scraping_kit.utils import split_list
from scraping_kit.utils_loader import load_db_and_bots
from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.db.models.topics import get_topic_classes
from scraping_kit.const import TOPICS_FROM_TRENDS




def task_trends(trend_names: List[str], n_text_context: int, nro_process: int):
    path_data = Path("data")
    db_tw = DBTwitter(path_data, "scrape_tw")
    topics_1_to_topics_2, topics_1 = get_topic_classes(db_tw.path_topic_classes)
    print("~"*10)
    print(f"----- Initialize process: {nro_process} -----")
    db_tw.create_topics_trends(trend_names, topics_1_to_topics_2, topics_1, n_text_context, nro_process)


def main_trends(trend_names: List[str], n_process: int, n_text_context: int) -> None:
    list_trend_names = split_list(trend_names, n_process)
    
    processes = []
    for nro_process, trend_names in enumerate(list_trend_names):
        if len(trend_names) != 0:
            p = multiprocessing.Process(
                target = task_trends,
                args = (
                    trend_names,
                    n_text_context,
                    nro_process,
                )
            )
            processes.append(p)
            p.start()
    for p in processes:
        p.join()


if __name__ == "__main__":
    n_process = int(sys.argv[1])
    process_type = str(sys.argv[2])
    
    n_text_context = 8
    MAX_WORKERS = 20

    db_tw, bots = load_db_and_bots()
    if process_type == TOPICS_FROM_TRENDS:
        failed_requests = db_tw.collect_searchs_topics(bots, MAX_WORKERS)
        trend_names = db_tw.get_trends_to_create_topics()
        main_trends(trend_names, n_process, n_text_context)