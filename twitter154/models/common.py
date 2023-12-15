from datetime import datetime

from pydantic import BaseModel, field_validator


class ValCommonModel(BaseModel):
    creation_date: datetime

    @field_validator('creation_date', mode="before")
    def parse_fecha_creacion(cls, date_str):
        if isinstance(date_str, str):
            try:
                return datetime.strptime(date_str, '%a %b %d %H:%M:%S %z %Y')
            except ValueError:
                raise ValueError(f"Invalid format date: {date_str}")
