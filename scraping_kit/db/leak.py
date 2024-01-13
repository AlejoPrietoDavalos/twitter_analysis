from typing import List

import numpy as np

from scraping_kit.db.db_twitter import DBTwitter
from scraping_kit.db.models.trends import Trends


def get_trend_names_uniques(
        db_tw: DBTwitter,
        not_in_topics: bool = True,
        not_in_searchs: bool = True
    ) -> List[str]:
    trend_names = []
    for trends_doc in db_tw.coll.trends.find():
        trends = Trends(**trends_doc)
        for trend in trends.iter_trends():
            if not_in_topics:
                topic_by_trend = db_tw.coll.topics.find_one({"query": trend.name})
                cond_1 = topic_by_trend is None
            else:
                cond_1 = True

            if not_in_searchs:
                search_by_trend = db_tw.coll.search.find_one({"query": trend.name})
                cond_2 = search_by_trend is None
            else:
                cond_2 = True
            
            if cond_1 and cond_2:
                trend_names.append(trend.name)
    return list(np.unique(trend_names))
