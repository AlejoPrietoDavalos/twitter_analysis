from typing import Generator, Dict, List
from datetime import datetime, timedelta, timezone


def date_delta(date_i: datetime, date_f: datetime) -> Dict[str, datetime]:
    return {"$gte": date_i, "$lt": date_f}


def date_one_day(year: int, month: int, day: int) -> Dict[str, datetime]:
    date_i = datetime(year, month, day, tzinfo=timezone.utc)
    date_f = date_i + timedelta(days=1)
    return date_delta(date_i=date_i, date_f=date_f)


def iter_dates_delta_n_days_back(n_days_back: int = 7, date_now: datetime = "now") -> Generator[List[Dict[str, datetime]], None, None]:
    assert isinstance(n_days_back, int) and n_days_back > 0, "`n_days` have a positive integer."
    if date_now == "now":
        date_now = datetime.now()
    date_now = date_now.date()
    
    for _ in range(n_days_back):
        yield date_one_day(year=date_now.year, month=date_now.month, day=date_now.day)
        date_now -= timedelta(days=1)

def dates_delta_n_days_back(n_days_back: int = 7, date_now: datetime = "now") -> List[Dict[str, datetime]]:
    """ Returns a list of date ranges, starting with the `date_now` and `n_days_back`."""
    dates = [date for date in iter_dates_delta_n_days_back(n_days_back=n_days_back, date_now=date_now)]
    return dates

