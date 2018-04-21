# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.loader import ItemLoader
import SecondHandHouse.items
import webbrowser
import urllib.request
from scrapy.http import FormRequest


class AnjukeSpider(scrapy.Spider):
    name = 'Anjuke'
    allowed_domains = ['beijing.anjuke.com']
    start_urls = ['https://beijing.anjuke.com/sale/']

    def parse(self, response):
        # 验证码处理部分
        # next page link
        next_url = response.xpath('//*[@class="multi-page"]/a[last()]/@href').get()
        print('*********' + str(next_url) + '*********')
        if next_url:
            yield scrapy.Request(url=next_url, callback=self.parse)
        # 爬取每一页的所有房屋连接
        num = len(response.xpath('//*[@id="houselist-mod-new"]/li').extract())
        for i in range(1, num + 1):
            url = response.xpath(
                '//*[@id="houselist-mod-new"]/li[{}]//div[@class="house-title"]/a/@href'.format(i)).get()
            yield scrapy.Request(url, callback=self.parse_detail)

    def parse_detail(self, response):
        houseinfo = response.xpath('//*[@class="houseInfo-wrap"]')
        if houseinfo:
            l = ItemLoader(SecondHandHouse.items.SecondhandhouseItem(), houseinfo)
            l.add_xpath('mode', '//div/div[2]/dl[1]/dd/text()')
            l.add_xpath('area', '//div/div[2]/dl[2]/dd/text()')
            l.add_xpath('floor', '//div/div[2]/dl[4]/dd/text()')
            l.add_xpath('age', '//div/div[1]/dl[3]/dd/text()')
            l.add_xpath('price', '//div/div[3]/dl[2]/dd/text()')
            l.add_xpath('location', '//div/div[1]/dl[1]/dd/a/text()')
            l.add_xpath('district', '//div/div[1]/dl[2]/dd/p/a[1]/text()')
            yield l.load_item()
