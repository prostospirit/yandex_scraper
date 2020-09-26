# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


import scrapy


class YandexReviewsParserItem(scrapy.Item):
    id = scrapy.Field()
    data = scrapy.Field()
    text = scrapy.Field()
    author = scrapy.Field()
    date = scrapy.Field()
    rating = scrapy.Field()
    comments = scrapy.Field()