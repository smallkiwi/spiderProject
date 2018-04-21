# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AnjukespiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    table = 'houseinfo'
    url = scrapy.Field()
    estate = scrapy.Field()
    locs = scrapy.Field()
    age = scrapy.Field()
    type = scrapy.Field()
    mode = scrapy.Field()
    area = scrapy.Field()
    direct = scrapy.Field()
    floor = scrapy.Field()
    level = scrapy.Field()
    price = scrapy.Field()
    downpay = scrapy.Field()
    monthpay = scrapy.Field()
