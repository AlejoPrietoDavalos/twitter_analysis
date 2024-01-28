from datetime import datetime

from pymongo.results import InsertOneResult

from scraping_kit import DBTwitter, BotScraper, date_one_day
from scraping_kit.db.models.raw import RawData
from scraping_kit.db.models.trends import Trends
from scraping_kit.utils import format_yyyy_xx
from scraping_kit.twitter_trends.params import ArgsTwitterTrends


def process_trends_raw_data(db_tw: DBTwitter, insert_one_result_raw: InsertOneResult) -> InsertOneResult:
    raw_data = db_tw.coll.raw.find_one(insert_one_result_raw.inserted_id)
    raw_data = RawData(**raw_data)
    trends = Trends.from_raw(raw_data)
    insert_one_result_trend = db_tw.coll.trends.insert_one(trends.model_dump())     # TODO: Check its ok.
    return insert_one_result_trend


def requests_and_process(db_tw: DBTwitter, bot: BotScraper, woeid: str = None) -> InsertOneResult:
    date_now = datetime.now().date()
    date_now = date_one_day(date_now.year, date_now.month, date_now.day)
    trends = db_tw.coll.trends_from_date_range(date_now)
    # FIXME: Revisa que sea el primer trend, y sino retorna None.

    if trends is not None:
        msg = f"You already have a Trends on the date: "
        d = trends.created
        d = format_yyyy_xx(*d.timetuple()[:6]).split("_")
        format_d = lambda yyyy,mm,dd,HH,MM,SS: f"{yyyy}-{mm}-{dd} {HH}:{MM}:{SS}"
        d = format_d(*d)
        
        msg += d
        print(msg)
        print("You don't need to download again.")
        return None
    else:
        req_args = ArgsTwitterTrends.from_woeid(woeid)
        insert_one_result_raw = db_tw.requests_and_save(req_args, bot)
        insert_one_result_trend = process_trends_raw_data(db_tw, insert_one_result_raw)
        db_tw.coll.change_is_processed(insert_one_result_raw)
        print("Trends download successful.")
        return insert_one_result_trend
