""" `python3 search_to_topic_subprocess.py n_process`"""
from typing import List, Any
from datetime import datetime, timedelta, timezone
from pathlib import Path
import multiprocessing
import sys

from scraping_kit.dl import instance_classifier
from scraping_kit.utils import split_list, get_datetime_now
from scraping_kit.utils_loader import load_db_and_bots, load_profiles
from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.db.models.user_full import TopicUser, TopicUserClasses
from scraping_kit.db.models.topics import get_topic_classes
from scraping_kit.const import TOPICS_FROM_USERS


def task_users(profiles: List[str], ctx: int, nro_process: int):
    print("~"*10)
    print(f"----- Initialize process: {nro_process} -----")
    len_profiles = len(profiles)
    idx = 1

    path_data = Path("data")
    db_tw = DBTwitter(path_data, "scrape_tw")
    topics_1_to_topics_2, topics_1 = get_topic_classes(db_tw.path_topic_classes)
    
    classifier = instance_classifier()
    date_now = get_datetime_now().replace()
    date_i = date_now - timedelta(days=14)
    date_i = date_i
    for profile in profiles:
        user_full = db_tw.get_user_full_data(profile, date_i, date_now)
        topic_user: TopicUser = user_full.topics_user
        topic_user.creation_date = topic_user.creation_date.replace(tzinfo=timezone.utc)
        dt = date_now - topic_user.creation_date
        dt = abs(dt.days)
        
        if len(user_full.tweets_user) > 0:
            texts_joined = "\n".join(user_full.get_texts(ctx))
            if topic_user.topics_1 is None or dt>14:
                topics_classes_1 = TopicUserClasses.from_texts(
                    texts_joined,
                    classifier,
                    topics_1,
                    ctx
                )
                topic_user.topics_1 = topics_classes_1
                db_tw.coll.topics_user.update_one({"profile": user_full.profile}, {"$set": topic_user.model_dump()})
            if (topic_user.topics_2 is None and topic_user.topics_1 is not None) or dt>14:
                l1, l2 = topic_user.topics_1.labels[:2]
                topics_classes_2 = TopicUserClasses.from_texts(
                    texts_joined,
                    classifier,
                    topics_1_to_topics_2[l1] + topics_1_to_topics_2[l2],
                    ctx
                )
                topic_user.topics_2 = topics_classes_2
                db_tw.coll.topics_user.update_one({"profile": user_full.profile}, {"$set": topic_user.model_dump()})
        print(f"{idx}/{len_profiles} - {profile}")
        idx += 1
        
    
    


def main_users(profiles: List[str], n_process: int, ctx: int) -> None:
    list_profiles = split_list(profiles, n_process)
    
    processes = []
    for nro_process, profiles in enumerate(list_profiles):
        if len(profiles) != 0:
            p = multiprocessing.Process(
                target = task_users,
                args = (
                    profiles,
                    ctx,
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
    
    ctx = 5
    MAX_WORKERS = 20

    if process_type == TOPICS_FROM_USERS:
        db_tw, bots = load_db_and_bots()
        profiles = load_profiles()
        db_tw.collect_usertimeline(profiles, bots, MAX_WORKERS)

        profiles_leaked = []
        for profile in profiles:
            user = db_tw.find_user(profile, with_suspended=False)
            if user is not None:
                topic_user = db_tw.get_topic_user(user)
                if topic_user.topics_1 is None or topic_user.topics_2 is None:
                    profiles_leaked.append(profile)
        main_users(profiles_leaked, n_process, ctx)