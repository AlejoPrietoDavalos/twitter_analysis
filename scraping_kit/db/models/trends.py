from __future__ import annotations
from datetime import datetime, timezone
from typing import List

import pandas as pd
from pydantic import BaseModel, field_validator

from scraping_kit.db.models.raw import RawData


class TrendCreatedAt(BaseModel):
    created_at: int
    created_at_v1: str

class LocationTrend(BaseModel):
    name: str
    woeid: int

class GroupedTrend(BaseModel):
    name: str
    query: str
    url: str

class Trend(GroupedTrend):
    volume: int
    volumeShort: str
    domainContext: str
    groupedTrends: List[GroupedTrend]

class Trends(BaseModel):
    trends: List[Trend]
    location: LocationTrend
    created: datetime

    @classmethod
    def from_raw(cls, raw_data: RawData) -> Trends:
        r_json = raw_data.response_json
        r_json["trends"] = [t for t_idx, t in r_json["trends"].items()]
        return Trends(**r_json)

    def get_df(self) -> pd.DataFrame:
        rows = []
        for trend in self.trends:
            model_dump_ = trend.model_dump()
            model_dump_.pop("groupedTrends")
            model_dump_.pop("volumeShort")
            rows.append(model_dump_)
        df = pd.DataFrame(rows)
        df.sort_values("volume", ascending=False, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    @field_validator('created', mode="before")
    def parse_fecha_creacion(cls, created: dict | datetime):
        if isinstance(created, dict):
            try:
                return datetime.fromtimestamp(created["created_at"], tz=timezone.utc)
            except ValueError:
                raise ValueError(f"Invalid format date: {created}")
        elif isinstance(created, datetime):
            return created.replace(tzinfo=timezone.utc)
        else:
            raise Exception("Valor Inválido.")