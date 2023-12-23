from typing import Literal, Tuple
from abc import ABC, abstractclassmethod
import requests
from requests import Response
from datetime import datetime

from pydantic import BaseModel


class ReqArgs(BaseModel, ABC):
    method: Literal["GET", "POST"] = "GET"

    @abstractclassmethod
    def endpoint_name(cls) -> str:
        """ Endpoint name."""
        ...

    @abstractclassmethod
    def url(cls) -> str:
        """ Endpoint URL."""
        ...
    
    def response_dump(self) -> dict:
        model_dump_ = super().model_dump()
        model_dump_["url"] = self.url()
        return model_dump_

    def model_dump(self) -> dict:
        model_dump_ = super().model_dump()
        model_dump_["endpoint_name"] = self.endpoint_name()
        model_dump_["url"] = self.url()
        return model_dump_

