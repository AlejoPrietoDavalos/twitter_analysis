from scraping_kit.bot_scraper import Headers, BotScraper

class HeaderTwitterTrends(Headers):
    @classmethod
    def get_header(cls, bot_scraper: BotScraper) -> dict:
        return {
            "content-type": "application/x-www-form-urlencoded",
            "X-RapidAPI-Key": bot_scraper.credential,
            "X-RapidAPI-Host": "twitter-trends5.p.rapidapi.com"
        }
