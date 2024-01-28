from typing import Tuple, List
from datetime import datetime
from pathlib import Path
import subprocess
import os

import pandas as pd

from scraping_kit.utils import format_yyyy_xx, get_datetime_now
from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.bot_scraper import BotList

def load_db_and_bots(
        path_data: Path = None,
        db_name: str = "scrape_tw",
        verbose = False
    ) -> Tuple[DBTwitter, BotList]:
    if path_data is None:
        path_data = Path("data")

    try:
        db_tw = DBTwitter(path_data, db_name)
        db_tw.db["test"].find_one()
        bots = db_tw.load_bots()
        print("Database and bots loaded correctly.")
    except:
        print("Error: You need to run the server. You can check it at http://localhost:27017/")

    if verbose:
        print(f"Collection Names: {db_tw.db.list_collection_names()}")
        print(f"Bots: {bots}")
    return db_tw, bots


def load_profiles(file_name: str, column_name: str = "screenName", path_input: Path = None) -> List[str]:
    if path_input is None:
        path_input = Path("input")
    try:
        df = pd.read_excel(path_input / file_name)
    except:
        files_into_input = ' | '.join([p.name for p in path_input.iterdir()])
        print(f"Incorrect file name '{file_name}'. There are ~~> '{files_into_input}'.")
        return None
    try:
        profiles = df[column_name].to_list()
    except:
        print(f"Incorrect name column, searching for '{column_name}', writing error.")
        return None
    print(f"Name of users loaded correctly. total={len(profiles)}")
    return profiles

def save_db(db_name: str = "scrape_tw", folder_backup: str = "data/backup_db") -> None:
    date_now = get_datetime_now()
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