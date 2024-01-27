from typing import Tuple, List
from datetime import datetime
from pathlib import Path
import subprocess
import os

import pandas as pd

from scraping_kit.utils import format_yyyy_xx
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


def load_profiles(path_data: Path = None) -> List[str]:
    """ TODO: Ask Vera how she wants to import the users to study."""
    if path_data is None:
        path_data = Path("data")
    df = pd.read_excel(path_data / "twitter_accounts.xlsx")
    df = df.sort_values("followersCount", ascending=False)
    profiles = df["screenName"].to_list()
    return profiles

def save_db(db_name: str = "scrape_tw", folder_backup: str = "data/backup_db") -> None:
    date_now = datetime.now()
    date_now = format_yyyy_xx(*date_now.timetuple()[:6])
    path_out_db = f"{folder_backup}/date_{date_now}"
    process = subprocess.run(
        ["mongodump", "--db", db_name, "--out", path_out_db],
        stderr = subprocess.DEVNULL,
        stdin = subprocess.DEVNULL
    )
    if process.returncode == 0:
        print(f"Database saved into: {path_out_db}")
    else:
        print("Failed to connect to server, run_server.")

def run_server(path_db: str = "~/.data/db") -> None:
    subprocess.Popen(
        f"mongod --dbpath '{path_db}'",
        shell = True,
        stdin = subprocess.DEVNULL,
        stdout = subprocess.DEVNULL
    )
    print("Server running. You can review it by entering: http://localhost:27017/")