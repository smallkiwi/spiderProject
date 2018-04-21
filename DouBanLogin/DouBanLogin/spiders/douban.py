# -*- coding: utf-8 -*-
import scrapy
import webbrowser
from scrapy.http import Request, FormRequest
import urllib.request, urllib

class DoubanSpider(scrapy.Spider):
    name = 'douban'
    allowed_domains = ['www.douban.com']
    # start_urls = ['http://www.douban.com/']
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3236.0 Safari/537.36"}

    def start_requests(self):
        return [FormRequest('https://accounts.douban.com/login', headers=self.header, meta={"cookiejar": 1},
                            callback=self.parse)]

    def parse(self, response):
        captcha = response.xpath('//*[@id="captcha_image"]/@src').extract_first()
        id = response.xpath('//input[@name="captcha-id"]/@value').extract_first()
        print(id)
        if captcha:
            print("此处有验证码.")
            localpath = r'./captcha.png'
            urllib.request.urlretrieve(captcha, filename=localpath)
            webbrowser.open(localpath)  # 非系统默认浏览器打开
            captcha_value = input("查看验证码是:")
            return [
                FormRequest.from_response(response, meta={'cookiejar': response.meta['cookiejar']}, headers=self.header,
                                          formdata={
                                              'source': 'None',
                                              'form_email': '707739450@qq.com',
                                              'form_password': '123456mai',
                                              'captcha-solution': captcha_value,
                                              'captcha-id': id,
                                              'login': '登录',
                                              'redir': 'https://www.douban.com/'
                                          },
                                          callback=self.after_login,
                                          dont_filter=True)]
        else:
            return [
                FormRequest.from_response(response, meta={'cookiejar': response.meta['cookiejar']}, headers=self.header,
                                          formdata={
                                              'source': 'None',
                                              'form_email': '707739450@qq.com',
                                              'form_password': '123456mai',
                                              'login': '登录',
                                              'redir': 'https://www.douban.com'
                                          },
                                          callback=self.after_login,
                                          dont_filter=True)]

    def after_login(self, response):
        author_link = response.xpath('//*[@class="stream-items"]//div[@class="text"]/a/@href').extract()
        for link in author_link:
            print(link)





