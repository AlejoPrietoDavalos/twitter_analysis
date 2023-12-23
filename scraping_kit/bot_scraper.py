from __future__ import annotations
from typing import Type, List, Tuple, Callable
from pathlib import Path
import json
import requests
from requests import Response
from datetime import datetime

from pydantic import BaseModel, Field

from scraping_kit.requests_args import ReqArgs


class BotScraper(BaseModel):
    acc_name: str = Field(frozen=True)
    credential: str = Field(frozen=True, repr=False)

    def get_response(self, req_args: Type[ReqArgs], fn_headers: Callable) -> Tuple[Response, datetime]:
        response = requests.request(**req_args.response_dump(), headers=fn_headers(self))
        date_now = datetime.now()
        return response, date_now

def load_bots(path_acc: Path) -> List[BotScraper]:
    with open(path_acc) as f:
        return [BotScraper(**acc_json) for acc_json in json.load(f)]
