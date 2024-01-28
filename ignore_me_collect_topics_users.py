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
from scraping_kit.utils_topics import get_topic_classes
from scraping_kit.const import TOPICS_FROM_USERS
from scraping_kit.utils_topics import get_classes_2

def task_users(
        profiles: List[str],
        nro_process: int,
        days_to_update_topics: int,
        min_tweets_to_classify: int = 3,
        max_tweets_to_classify: int = 15
    ) -> None:
    print("~"*10)
    print(f"----- Initialize process: {nro_process} -----")
    len_profiles = len(profiles)
    idx = 1

    path_data = Path("data")
    db_tw = DBTwitter(path_data, "scrape_tw")
    classes_1_to_2, classes_1 = get_topic_classes(db_tw.path_topic_classes)
    
    classifier = instance_classifier()
    date_now = get_datetime_now().replace()
    date_i = date_now - timedelta(days=days_to_update_topics)
    date_i = date_i
    for profile in profiles:
        user_full = db_tw.get_user_full_data(profile, date_i, date_now)
        topic_user: TopicUser = user_full.topics_user
        topic_user.creation_date = topic_user.creation_date.replace(tzinfo=timezone.utc)
        dt = date_now - topic_user.creation_date
        dt = abs(dt.days)
        
        if len(user_full.tweets_user) > 0:
            texts = user_full.get_texts()[:max_tweets_to_classify]
            if len(texts) >= min_tweets_to_classify and (topic_user.topics_1 is None or dt > days_to_update_topics):
                topic_user.topics_1 = TopicUserClasses.from_texts(texts, classifier, classes_1)
                db_tw.coll.topics_user.update_one({"profile": user_full.profile}, {"$set": topic_user.model_dump()})
            if len(texts) >= min_tweets_to_classify and ((topic_user.topics_2 is None and topic_user.topics_1 is not None) or dt > days_to_update_topics):
                classes_2 = get_classes_2(topic_user.topics_1.labels, classes_1_to_2)
                topic_user.topics_2 = TopicUserClasses.from_texts(texts, classifier, classes_2)
                db_tw.coll.topics_user.update_one({"profile": user_full.profile}, {"$set": topic_user.model_dump()})
        
        msg_1 = None if topic_user.topics_1 is None else topic_user.topics_1.labels[:2]
        msg_2 = None if topic_user.topics_2 is None else topic_user.topics_2.labels[:2]
        print(f"{idx}/{len_profiles} | profile={profile} | topics_1={msg_1} | topics_2={msg_2}")
        idx += 1
        
    
    


def main_users(
        profiles: List[str],
        n_process: int,
        days_to_update_topics: int = 14,
        min_tweets_to_classify: int = 3,
        max_tweets_to_classify: int = 15
    ) -> None:
    list_profiles = split_list(profiles, n_process)
    
    processes = []
    for nro_process, profiles in enumerate(list_profiles):
        if len(profiles) != 0:
            p = multiprocessing.Process(
                target = task_users,
                args = (
                    profiles,
                    nro_process,
                    days_to_update_topics,
                    min_tweets_to_classify,
                    max_tweets_to_classify
                )
            )
            processes.append(p)
            p.start()
    for p in processes:
        p.join()


if __name__ == "__main__":
    n_bests_users = int(sys.argv[1])
    days_to_update_topics = int(sys.argv[2])
    file_name = str(sys.argv[3])
    min_tweets_to_classify = int(sys.argv[4])
    max_tweets_to_classify = int(sys.argv[5])
    n_process = int(sys.argv[6])
    process_type = str(sys.argv[7])
    MAX_WORKERS = int(sys.argv[8])

    if process_type == TOPICS_FROM_USERS:
        db_tw, bots = load_db_and_bots()
        profiles = load_profiles(file_name)
        db_tw.collect_usertimeline(profiles, bots, MAX_WORKERS)

        if n_bests_users != -1:
            users = db_tw.get_user_list(profiles)
            users.keep_bests(n_bests_users)
            profiles = [user.profile for user in users]

        profiles_leaked = []
        for profile in profiles:
            user = db_tw.find_user(profile, with_suspended=False)
            if user is not None:
                topic_user = db_tw.get_topic_user(user)
                if topic_user.topics_1 is None or topic_user.topics_2 is None:
                    profiles_leaked.append(profile)
        print("~"*20)
        print(f"~~> Number of profiles to collect topics: {len(profiles_leaked)}")
        print("~"*20)
        main_users(profiles_leaked, n_process, days_to_update_topics, min_tweets_to_classify, max_tweets_to_classify)