# -*- coding: utf8 -*-
import scrapy
import js2py
import json
import math
import logging

from scrapy.http.request.json_request import JsonRequest

from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from ..items import YandexReviewsParserItem


class ReviewsSpider(scrapy.Spider):
    name = 'yandex'
    allowed_domains = ['yandex.by']
    start_urls = ['https://yandex.by/maps/org/sosedi/1042256439/']
    file_format = 'json'
    custom_settings = {
        'LOG_FILE': f'logs/{name}.log',
        'LOG_LEVEL': 'DEBUG',  # INFO DEBUG
        'FEED_EXPORT_ENCODING': 'UTF-8',
        'FEED_FORMAT': file_format,
        'FEED_URI': f'results/{name}.{file_format}',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.review_url = 'https://yandex.by/maps/api/business/fetchReviews'
        self.json_script_xpath = '/html/body/script[@type="application/json"]/text()'
        self.page_size = 50
        self.stats = '{"l":"ru","m":"wide","r":"16.8.4","s":"ugc_maps","t":"maps","v":"2.19.1","dnt":"1"}'
        self.sid = '652db17c-350c-485b-8458-9ef7490db375'

    def parse(self, response):
        json_data = json.loads(response.xpath(self.json_script_xpath).get())
        param = self._collect_params(json_data)
        page_quantity = math.ceil(param['review_count'] / self.page_size)

        for page in range(1, page_quantity + 1):
            param['s'] = self._s_parameter(param)
            api_review_url = f"{self.review_url}?ajax=1&businessId={param['businessId']}&" \
                             f"csrfToken={param['csrfToken']}&page={param['page']}&pageSize={self.page_size}&" \
                             f"ranking=by_relevance_org&reqId={param['reqId']}&" \
                             f"s={param['s']}&sessionId={param['sessionId']}"

            yield response.follow(url=api_review_url, callback=self.parse_reviews, cb_kwargs=param)

    def parse_reviews(self, response, param):
        reviews = json.loads(response.text)
        if reviews.get('error'):
            self.log(reviews['error']['message'], level=logging.ERROR)
        else:
            headers = {
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                              'Chrome/85.0.4183.121 Safari/537.36',
                'x-balancing-hash': '1453054966',
                'x-cmnt-api-key': param['api_key'],
                'x-yandex-appinfo': 'eyJ2ZXJzaW9uIjoiMi4xOS4xIn0=',
                'x-yandex-sourceservice': 'ugc_maps'
            }
            for review in reviews['data']['reviews']:
                item = YandexReviewsParserItem()
                item['review_id'] = review['reviewId']
                item['review_text'] = review['text']
                item['review_author'] = review['author']['name']
                item['review_date'] = review['updatedTime']
                item['rating'] = review['rating']
                yield item

                if review['hasComments']:
                    comments_url = f'https://yandex.by/comments/api/v1/tree?stats={self.stats}' \
                                   f'&entityId={review["reviewId"]}' \
                                   f'&sid={self.sid}&allowAbsent=true&supplierServiceSlug=ugc'
                    yield JsonRequest(url=comments_url, callback=self.parse_comments, headers=headers)

    def parse_comments(self, response):
        comments = json.loads(response.text)['tree']
        print(comments)
        print(comments.keys())

    def errback_httpbin(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)

    def _s_parameter(self, param):
        e = f"ajax=1&businessId={param['business_id']}&csrfToken={param['csrfToken'].replace(':', '%3A')}" \
            f"&page={param['page']}&pageSize={self.page_size}&ranking=by_relevance_org" \
            f"&reqId={param['reqId']}&sessionId={param['sessionId']}"
        f = js2py.eval_js("function (e) {for (var t = e.length, n = 5381, r = 0; r < t; r++) "
                          "{n = 33 * n ^ e.charCodeAt(r);} "
                          "return n >>> 0}")
        return f(e)

    def _collect_params(self, json_data):
        token = json_data['csrfToken']
        session_id = json_data['counters']['analytics']['sessionId']
        request_id = json_data['orgpagePreloadedResults']['requestId']
        api_key = json_data['commentatorWidget']['apiKey']
        review_count = json_data['orgpagePreloadedResults']['items'][0]['ratingData']['reviewCount']
        business_id = json_data['query']['orgpage']['id']

        param = {'businessId': business_id, 'csrfToken': token, 'page': page, 'pageSize': self.page_size,
                 'ranking': 'by_relevance_org', 'reqId': request_id, 'sessionId': session_id,
                 'api_key': api_key, 'review_count': int(review_count)}

        return param