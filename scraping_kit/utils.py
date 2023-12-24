from typing import Generator, Tuple, List
from pathlib import Path
import random

from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.bot_scraper import BotScraper


def load_db_and_bots(path_data: Path, db_name: str, verbose=True) -> Tuple[DBTwitter, List[BotScraper]]:
    db_tw = DBTwitter(path_data, db_name)
    bots = db_tw.load_bots()
    if verbose:
        print(f"Collection Names: {db_tw.db.list_collection_names()}")
        print(f"Bots: {bots}")
    return db_tw, bots


T_BotChoiced = Tuple[int, BotScraper]

def random_bot(bots: List[BotScraper]) -> T_BotChoiced:
    idx = random.randint(0, len(bots) - 1)
    return idx, bots[idx]


def iter_random_bot(bots: List[BotScraper], n_iters: int) -> Generator[T_BotChoiced, None, None]:
    return (random_bot(bots) for _ in range(n_iters))