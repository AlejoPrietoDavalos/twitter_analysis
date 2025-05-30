from typing import Generator, Dict, List, Any
from datetime import datetime, timedelta, timezone


def get_datetime(year: int, month: int, day: int) -> datetime:
    return datetime(year=year, month=month, day=day, tzinfo=timezone.utc)

def get_datetime_now() -> datetime:
    return datetime.now(tz=timezone.utc)

def split_list(list_complety: List[Any], n_fragments: int) -> List[List[Any]]:
    if n_fragments <= 0:
        raise ValueError("El número de fragmentos debe ser mayor que cero.")

    fragment = len(list_complety) // n_fragments
    rest = len(list_complety) % n_fragments

    list_fragment = []
    for i in range(n_fragments):
        frag = list_complety[i * fragment + min(i, rest):(i + 1) * fragment + min(i + 1, rest)]
        list_fragment.append(frag)
    return list_fragment


def date_delta(date_i: datetime, date_f: datetime) -> Dict[str, datetime]:
    return {"$gte": date_i, "$lt": date_f}


def date_one_day(year: int, month: int, day: int) -> Dict[str, datetime]:
    date_i = get_datetime(year=year, month=month, day=day)
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


def format_yyyy_xx(year: int, *xx) -> str:
    return "_".join([str(year).zfill(4)] + [str(xx_).zfill(2) for xx_ in xx])

def format_yyyy_mm_dd(year: int, month: int, day: int) -> str:
    return format_yyyy_xx(year, month, day)

def format_date_yyyy_mm_dd(date: datetime) -> str:
    return format_yyyy_mm_dd(*date.timetuple()[:3])

def format_date_full(date: datetime, n_elems=7) -> str:
    """
    - n_elems==6 -> from year to ms.
    - n_elems==3 -> from year to day.
    """
    return format_yyyy_xx(*date.timetuple()[:n_elems])