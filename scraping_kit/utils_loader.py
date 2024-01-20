from typing import Tuple
from pathlib import Path
from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.bot_scraper import BotList

def load_db_and_bots(
        path_data: Path = None,
        db_name: str = "scrape_tw",
        verbose=True
    ) -> Tuple[DBTwitter, BotList]:
    if path_data is None:
        path_data = Path("data")
    db_tw = DBTwitter(path_data, db_name)
    bots = db_tw.load_bots()
    if verbose:
        print(f"Collection Names: {db_tw.db.list_collection_names()}")
        print(f"Bots: {bots}")
    return db_tw, bots