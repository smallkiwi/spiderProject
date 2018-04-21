# -*- coding: utf-8 -*-
from scrapy import Request
from scrapy import Selector
from selenium import webdriver
from AnjukeSpider.items import AnjukespiderItem
from scrapy_redis.spiders import RedisSpider
import redis

r = redis.Redis(host='10.36.131.167', port=6379)


class ShenzhenSpider(RedisSpider):
    name = 'shenzhen'
    # 注意redis-key格式:爬虫
    redis_key = "shenzhenspider:start_urls"  # 这个变量名可以任意修改

    # 初始化webdriver
    def __init__(self, *args, **kwargs):
        self.driver = webdriver.Chrome()
        # 动态定义允许的域列表
        # domain = kwargs.pop('domain', '')
        # self.allowed_domains = filter(None, domain.split(','))
        super(ShenzhenSpider, self).__init__(*args, **kwargs)

    def __del__(self):
        if self.driver is not None:
            self.driver.quit()

    def parse(self, response):
        # 翻页
        next_url = response.xpath('//*[@class="multi-page"]/a[last()]/@href').get()
        print('*********' + str(next_url) + '*********')
        if next_url:
            # lpush shenzhenspider:start_urls https://shenzhen.anjuke.com/sale/
            r.lpush("shenzhenspider:start_urls", next_url)
        # 爬取每一页的房屋链接
        house_list = response.xpath('//*[@id="houselist-mod-new"]/li')
        for house in house_list:
            url = house.xpath('.//div[@class="house-title"]/a/@href').get()
            yield Request(url=url, callback=self._parse_handler)

    def _parse_handler(self, response):
        # 通过self.driver.get(response.url)就能使用selenium下载内容，如果直接使用response中的网页内容是静态的
        self.driver.get(response.url)
        selector = Selector(text=self.driver.page_source)  # 网页解析
        houseinfo = selector.xpath('//div[contains(@class,"houseInfo-wrap")]')
        if houseinfo:
            info = AnjukespiderItem()
            info['url'] = response.url
            info['estate'] = houseinfo.xpath('.//div[contains(@class,"first-col")]/dl[1]/dd/a/text()').get()
            info['locs'] = ''.join(
                houseinfo.xpath('.//div[contains(@class,"first-col")]/dl[2]/dd/p/a/text()').extract())
            info['age'] = houseinfo.xpath('.//div[contains(@class,"first-col")]/dl[3]/dd/text()').get()
            info['type'] = houseinfo.xpath('.//div[contains(@class,"first-col")]/dl[4]/dd/text()').get()
            info['mode'] = (houseinfo.xpath('.//div[contains(@class,"second-col")]/dl[1]/dd/text()').get()).replace(
                '\t', '').replace('\n', '')
            info['area'] = houseinfo.xpath('.//div[contains(@class,"second-col")]/dl[2]/dd/text()').get()
            info['direct'] = houseinfo.xpath('.//div[contains(@class,"second-col")]/dl[3]/dd/text()').get()
            info['floor'] = (houseinfo.xpath('.//div[contains(@class,"second-col")]/dl[4]/dd/text()').get()).strip()
            info['level'] = houseinfo.xpath('.//div[contains(@class,"third-col")]/dl[4]/dd/text()').get()
            info['price'] = houseinfo.xpath('.//div[contains(@class,"third-col")]/dl[1]/dd//text()').get()
            info['downpay'] = (houseinfo.xpath('.//div[contains(@class,"third-col")]/dl[2]/dd//text()').get()).strip()
            info['monthpay'] = houseinfo.xpath('.//div[contains(@class,"third-col")]/dl[3]/dd//text()').get()
            yield info
