import os
from dotenv import load_dotenv
load_dotenv()

def get_headers() -> None:
    return {
        "content-type": "application/x-www-form-urlencoded",
        "X-RapidAPI-Key": os.getenv("X-RapidAPI-Key_2"),
        "X-RapidAPI-Host": "twitter-trends5.p.rapidapi.com"
    }
