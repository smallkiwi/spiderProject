# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import re
def list2str(value):
    new = ''.join(value).strip()
    return new

class SecondhandhousePipeline(object):
    def process_item(self, item, spider):
        area = item['area']
        price = item['price']
        loc = item['location']
        district = item['district']
        mode = item['mode']
        age = item['age']
        floor = item['floor']
        modes = list2str(mode)
        item['area'] = int(re.findall(r'\d+',list2str(area))[0])
        item['age'] = int(re.findall(r'\d+',list2str(age))[0])
        item['floor'] = list2str(floor)
        item['location'] = list2str(loc)
        item['district'] = list2str(district)
        item['price'] = int(re.findall(r'\d+',list2str(price))[0])
        item['mode'] = modes.replace('\t','').replace('\n','')
        return item
