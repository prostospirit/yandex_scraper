# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


import scrapy


class YandexReviewsParserItem(scrapy.Item):
    # name = scrapy.Field()
    review_id = scrapy.Field()
    data = scrapy.Field()
    review_text = scrapy.Field()
    review_author = scrapy.Field()
    review_date = scrapy.Field()
    rating = scrapy.Field()
    # parent_id = scrapy.Field()


class YandexReviewsCommentParserItem(scrapy.Item):
    review_id = scrapy.Field()  # link to review
    comment_id = scrapy.Field()
    comment_text = scrapy.Field()
    is_official = scrapy.Field()