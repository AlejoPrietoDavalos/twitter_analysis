""" https://rapidapi.com/alexanderxbx/api/twitter-api45"""
from __future__ import annotations
from typing import Type, Literal

from pydantic import BaseModel

from scraping_kit import ReqArgs, Headers
from scraping_kit.twitter45.headers import HeaderTwitter45


class BaseReqArgsTwitter45(ReqArgs):
    method: Literal["GET", "POST"] = "GET"

    @classmethod
    def header_cls(cls) -> Type[Headers]:
        return HeaderTwitter45


#----------------------------------------User Timeline----------------------------------------
class ParamsUserTimeline(BaseModel):
    screenname: str
    cursor: str = ""

class ArgsUserTimeline(BaseReqArgsTwitter45):
    """ This endpoint gets lates user's tweets by it's screenname."""
    params: ParamsUserTimeline
    
    @classmethod
    def endpoint_name(cls) -> str:
        return "user_timeline"

    @classmethod
    def url(cls) -> str:
        return "https://twitter-api45.p.rapidapi.com/timeline.php"
    
    @classmethod
    def from_screenname(cls, screenname: str, cursor: str = "") -> ArgsUserTimeline:
        params = ParamsUserTimeline(screenname=screenname, cursor=cursor)
        req_args = ArgsUserTimeline(params=params)
        return req_args

    @property
    def screenname(self) -> str:
        return self.params.screenname
#-------------------------------------User Timeline-------------------------------------



'''
#-------------------------------------Retweets-------------------------------------
#Get the list of of users who retweeted the tweet.
    @property
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/retweets.php"
#-------------------------------------Retweets-------------------------------------


#-------------------------------------Favorites-------------------------------------
#Get the list of users who liked the tweet.
    @property
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/favorites.php"
#-------------------------------------Favorites-------------------------------------


#-------------------------------------User info-------------------------------------
#Using this method you can get information about user by the screenname.
    @property
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/screenname.php"
#-------------------------------------User info-------------------------------------


#-------------------------------------Tweet info-------------------------------------
#With this endpoint you can get tweet info by it's id.
    @property
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/tweet.php"
#-------------------------------------Tweet info-------------------------------------


#-------------------------------------Following-------------------------------------
#Get the list of accounts user is following.
    @property
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/following.php"
#-------------------------------------Following-------------------------------------


#-------------------------------------Followers-------------------------------------
#Get latest user's followers list
    @property
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/followers.php"
#-------------------------------------Followers-------------------------------------
'''

#-------------------------------------Search-------------------------------------
class ParamsSearch(BaseModel):
    query: str
    cursor: str = ""

class ArgsSearch(BaseReqArgsTwitter45):
    """ Returns a search results for the specified query in Twitter search."""
    params: ParamsSearch
    
    @classmethod
    def endpoint_name(cls) -> str:
        return "search"
    
    @classmethod
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/search.php"
    
    @classmethod
    def from_trend_name(cls, trend_name: str, cursor: str = "") -> ParamsSearch:
        return ArgsSearch(params=ParamsSearch(query=trend_name, cursor=cursor))

#-------------------------------------Search-------------------------------------

'''
#-------------------------------------Check Retweet-------------------------------------
#This endpoint get latest tweets of the user and checks if there is a retweet of the needed tweet.
#WARNING: might not be suitable for old retweets.
    @classmethod
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/checkretweet.php"
#-------------------------------------Check Retweet-------------------------------------
'''


#-------------------------------------Check follow-------------------------------------
class ParamsCheckFollow(BaseModel):
    user: str
    follows: str

class ArgsCheckFollow(BaseReqArgsTwitter45):
    """
    - This endpoint get latest subscriptins of the user and latest followers for the target account. And checks if user follows the needed account.
    - WARNING: might not be suitable for big accounts or old subscriptions.
    """
    params: ParamsCheckFollow
    
    @classmethod
    def endpoint_name(cls) -> str:
        return "check_follow"

    @classmethod
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/checkfollow.php"
    
    @classmethod
    def from_profiles(cls, source: str, target: str) -> ArgsCheckFollow:
        """ True if `source` follow `target`."""
        return ArgsCheckFollow(params=ParamsCheckFollow(user=source, follows=target))
    
    @property
    def source(self) -> str:
        return self.params.user
    
    @property
    def target(self) -> str:
        return self.params.follows
#-------------------------------------Check follow-------------------------------------


'''
#-------------------------------------List timeline-------------------------------------
#With this endpoint you can get the timeline of the lists on Twitter.
    @classmethod
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/listtimeline.php"
#-------------------------------------List timeline-------------------------------------


#-------------------------------------User's likes-------------------------------------
#With this endpoint you can get user's latest likes.
    @classmethod
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/userlikes.php"
#-------------------------------------User's likes-------------------------------------

'''
#-------------------------------------User replies-------------------------------------
#Gets user's replies on twitter.
class ParamsUserReplies(BaseModel):
    screenname: str
    cursor: str = ""

class ArgsUserReplies(BaseReqArgsTwitter45):
    params: ParamsUserReplies

    @classmethod
    def endpoint_name(cls) -> str:
        return "user_replies"
    
    @classmethod
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/replies.php"

    @classmethod
    def from_screenname(cls, screenname: str, cursor="") -> ArgsUserReplies:
        return ArgsUserReplies(params=ParamsUserReplies(screenname=screenname, cursor=cursor))
    
    @property
    def screenname(self) -> str:
        return self.params.screenname
#-------------------------------------User replies-------------------------------------
'''

#-------------------------------------Check Like-------------------------------------
#This endpoint get latest like of the user and checks if there is a like of the needed tweet.
#WARNING: might not be suitable for the old likes.
    @classmethod
    def url(self) -> str:
        return "https://twitter-api45.p.rapidapi.com/checklike.php"
#-------------------------------------Check Like-------------------------------------
'''