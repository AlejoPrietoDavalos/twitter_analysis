from typing import List, Tuple
from pathlib import Path

from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.bot_scraper import BotScraper
from twitter_trends.headers import HeaderTwitterTrends
from twitter_trends.params import ArgsTwitterTrends, ParamsTwitterTrends


def load_db_and_bots(path_data: Path, db_name: str) -> Tuple[DBTwitter, List[BotScraper]]:
    db_tw = DBTwitter(path_data, db_name)
    bots = db_tw.load_bots()
    return db_tw, bots