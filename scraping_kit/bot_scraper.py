from typing import List
from pathlib import Path
import json

from pydantic import BaseModel, Field


class BotScraper(BaseModel):
    acc_name: str = Field(frozen=True)
    credential: str = Field(frozen=True, repr=False)

def load_bots(path_acc: Path) -> List[BotScraper]:
    with open(path_acc) as f:
        return [BotScraper(**j) for j in json.load(f)]
