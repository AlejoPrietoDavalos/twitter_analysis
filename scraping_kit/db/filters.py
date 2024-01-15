""" Tools for leak DB."""

def filter_profile(profile: str) -> dict:
    return {"profile": profile}

def filter_tweet_user(tweet_id: str) -> dict:
    return {"tweet_id": tweet_id}