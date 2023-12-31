from typing import Generator, Dict, List
from datetime import datetime, timedelta, timezone


def date_delta(date_i: datetime, date_f: datetime) -> Dict[str, datetime]:
    return {"$gte": date_i, "$lt": date_f}


def date_one_day(year: int, month: int, day: int) -> Dict[str, datetime]:
    date_i = datetime(year, month, day, tzinfo=timezone.utc)
    date_f = date_i + timedelta(days=1)
    return date_delta(date_i=date_i, date_f=date_f)


def iter_dates_by_range(date_from: datetime, date_to: datetime) -> Generator[Dict[str, datetime], None, None]:
    date_from, date_to = date_from.date(), date_to.date()
    assert date_from < date_to, "`date_to` must be greater"
    
    yield date_one_day(date_from.year, date_from.month, date_from.day)

    is_finish = False
    date_aux = date_from
    while not is_finish:
        date_aux += timedelta(days=1)
        yield date_one_day(date_aux.year, date_aux.month, date_aux.day)
        if date_aux >= date_to:
            is_finish = True
    
def dates_delta_n_days_back(date_from: datetime, date_to: datetime) -> List[Dict[str, datetime]]:
    """ Returns a list of date ranges, starting with the `date_now` and `n_days_back`."""
    return list(date for date in iter_dates_by_range(date_from, date_to))

