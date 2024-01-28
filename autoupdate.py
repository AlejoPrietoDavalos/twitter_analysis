"""
### Information for Vera:
- This script is executed by `autoupdate.sh`.
- If you want to rename the containing folder, or subfolders as "dev_stuff" in the future,
you must change the PATH inside `autoupdate.sh` for it to work. Or tell me and I'll do it for free.
- And you must also change the path of the .plist file, and copy it to /Library/LaunchDaemons.

# If one day you want this to stop working:
- You must delete the .plist file in the /Library/LaunchDaemons directory.
- Or tell me, and I'll do it =).
"""
from datetime import datetime

from scraping_kit.utils_loader import load_db_and_bots, run_server
from scraping_kit.utils import get_datetime_now

def print_log(date_now: datetime) -> None:
    t = str(date_now).split('.')[0]
    tz = date_now.tzname()
    print()
    print("#"*50)
    print("~"*50)
    print(f"Execution: {t} | {tz}")
    print("~"*50)


if __name__ == "__main__":
    # Print some logs inside "autoupdate_log.txt".
    date_now = get_datetime_now()
    print_log(date_now)

    # Run the server.
    run_server("/data/db")

    # Open the database and scraping bots.
    db_tw, bots = load_db_and_bots()

    # Collect today's trends and associated Tweets.
    db_tw.collect_trends_today(bots)