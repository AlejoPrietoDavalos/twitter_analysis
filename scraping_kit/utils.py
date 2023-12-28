from typing import Tuple, Dict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.bot_scraper import BotList


def load_db_and_bots(path_data: Path, db_name: str, verbose=True) -> Tuple[DBTwitter, BotList]:
    db_tw = DBTwitter(path_data, db_name)
    bots = db_tw.load_bots()
    if verbose:
        print(f"Collection Names: {db_tw.db.list_collection_names()}")
        print(f"Bots: {bots}")
    return db_tw, bots



def date_delta(date_i: datetime, date_f: datetime) -> Dict[str, datetime]:
    return {"$gte": date_i, "$lt": date_f}

def date_one_day(year: int, month: int, day: int) -> Dict[str, datetime]:
    date_i = datetime(year, month, day, tzinfo=timezone.utc)
    date_f = date_i + timedelta(days=1)
    return date_delta(date_i=date_i, date_f=date_f)