import os
from dotenv import load_dotenv
load_dotenv()

def get_headers() -> None:
    return {
        "X-RapidAPI-Key": os.getenv("X-RapidAPI-Key"),
        "X-RapidAPI-Host": "twitter-api45.p.rapidapi.com"
    }