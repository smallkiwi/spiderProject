# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
import random


# 随机使⽤预定义列表⾥的 User-Agent 类
class RandomUserAgent(object):

    def __init__(self, agents):
        # 使⽤初始化的 agents 列表
        self.agents = agents

    @classmethod
    def from_crawler(cls, crawler):
        # 获取 settings 的 USER_AGENT 列表并返回
        return cls(crawler.settings.getlist('USER_AGENTS'))

    def process_request(self, request, spider):
        # 随机设置 Request 报头 header 的 User-Agent
        request.headers.setdefault('User-Agent', random.choice(self.agents))
