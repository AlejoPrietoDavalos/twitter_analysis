from __future__ import annotations
from typing import List, NewType, Dict, Tuple, Generator
from functools import cached_property
from pathlib import Path

import nltk
from nltk.corpus import stopwords
from wordcloud import WordCloud, STOPWORDS
import pandas as pd
import igraph as ig

from scraping_kit.db.models.tweet_user import TweetUser

T_Keywords = NewType("T_KeyWords", Dict[str, int])

class KeyCol:
    WORDS = "words"
    NAME = "name"
    KEYWORDS = "keywords"
    FOLLOWERS = "followers"
    FOLLOWING = "following"
    ARROWS_IN = "arrows_in"
    ARROWS_OUT = "arrows_out"


def get_blacklist_words(path_extra_words: Path = None, col_words=KeyCol.WORDS) -> set:
    blacklist_words = set()
    blacklist_words.update(STOPWORDS)
    blacklist_words.update(stopwords.words('english'))
    if path_extra_words is not None:
        df_extra = pd.read_excel(path_extra_words)
        blacklist_words.update(df_extra[col_words].to_list())
    return blacklist_words

def keywords_update(keywords: T_Keywords, keywords_new: T_Keywords) -> None:
    """ Modifica `keywords` el primer diccionario con los contadores del segundo."""
    for kw, count in keywords_new.items():
        if kw in keywords:
            keywords[kw] += count
        else:
            keywords[kw] = count

def texts2keywords(wc: WordCloud, texts: List[str]) -> T_Keywords:
    keywords = {}
    if len(texts) != 0:
        for text in texts:
            keywords_new = wc.process_text(text)
            keywords_update(keywords, keywords_new)
    return keywords

def tweets2keywords(wc: WordCloud, tweets: List[TweetUser]) -> T_Keywords:
    keywords = {}
    if len(tweets) != 0:
        for tweet in tweets:
            keywords_new = wc.process_text(tweet.text)
            keywords_update(keywords, keywords_new)
    return keywords