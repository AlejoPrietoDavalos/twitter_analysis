from scraping_kit import Headers, BotScraper

class HeaderTwitter45(Headers):
    @classmethod
    def get_header(cls, bot_scraper: BotScraper) -> dict:
        return {
        "X-RapidAPI-Key": bot_scraper.credential,
        "X-RapidAPI-Host": "twitter-api45.p.rapidapi.com"
    }