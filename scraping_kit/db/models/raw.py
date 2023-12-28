from typing import Type
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator


class ValCommonModel(BaseModel):
    creation_date: datetime

    @field_validator('creation_date', mode="before")
    def parse_fecha_creacion(cls, date: str | datetime):
        if isinstance(date, str):
            try:
                return datetime.strptime(date, '%a %b %d %H:%M:%S %z %Y')
            except ValueError:
                raise ValueError(f"Invalid format date: {date}")
        elif isinstance(date, datetime):
            return date.replace(tzinfo=timezone.utc)
        else:
            raise Exception("Valor Inválido.")


class RawData(ValCommonModel):
    creation_date: datetime
    req_args: dict
    response_json: dict | None
    endpoint_name: str
    is_processed: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)
