from typing import Literal, Optional
from datetime import datetime

from pydantic import BaseModel

class Cursor(BaseModel):
    status: Literal["active"] = "active"
    profile: str
    next_cursor: Optional[str]      # TODO: Ver el caso None.
    creation_date: datetime         # Date for last update.

