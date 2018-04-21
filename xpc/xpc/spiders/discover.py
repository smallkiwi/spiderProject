# -*- coding: utf-8 -*-
import scrapy
from scrapy import Request
import json
from xpc.items import PostItem, ComposerItem, CommentItem, CopyrightItem


class DiscoverSpider(scrapy.Spider):
    name = 'discover'
    allowed_domains = ['www.xinpianchang.com']
    start_urls = ['http://www.xinpianchang.com/channel/index/sort-like']

    def parse(self, response):
        # 翻页
        next_url = response.xpath('//div[@class="page"]//a[last()]/@href').get()
        print('****************' + str(next_url) + '****************')
        if next_url:
            yield scrapy.Request(url=next_url, callback=self.parse)

        post_url = "http://www.xinpianchang.com/a%s"
        post_list = response.xpath('//ul[@class="video-list"]/li')
        for post in post_list:
            post_id = post.xpath('./@data-articleid').extract_first()  # extract()返回字符串列表
            request = Request(post_url % post_id, callback=self.parse_post)
            request.meta['pid'] = post_id
            request.meta['thumbnail'] = post.xpath('./a/img/@_src').get()
            yield request

    # 视频列表
    def parse_post(self, response):
        post = PostItem()
        post['preview'] = response.xpath('//div[@class="filmplay"]//img/@src').extract_first()
        post['pid'] = response.meta['pid']
        post['thumbnail'] = response.meta['thumbnail']  # 图片
        post['video'] = response.xpath('//video[@id="xpc_video"]/@src').get()  # 视频链接
        post['title'] = response.xpath('//*[@class="title-wrap"]/h3/text()').get()  # 标题
        post['category'] = response.xpath('//*[@class="cate v-center"]/text()').get()
        vf = response.xpath('//*[@class="video-format v-center"]/text()').get()
        post['video_format'] = vf.strip() if vf else ""
        post['created_at'] = response.xpath('//*[@class="update-time v-center"]//text()').get()
        post['play_counts'] = response.xpath('//i[contains(@class,"play-counts")]/text()').get().replace(',', '')
        post['like_counts'] = response.xpath('//span[contains(@class,"like-counts")]/text()').get().replace(',', '')
        post['description'] = response.xpath('//p[contains(@class,"desc")]/text()').get() or ''
        yield post
        self.logger.info('scraped post(%s): %s' % (post['pid'], post['title']))

        # 视频与导演,一对多的关系
        compose_url = "http://www.xinpianchang.com/u%s"
        composer_list = response.xpath('//div[@class="user-team"]//ul[@class="creator-list"]/li')
        for composer in composer_list:
            cid = composer.xpath('./a/@data-userid').get()
            copyright = {
                'pcid': '%s_%s' % (post['pid'], cid),
                'pid': post['pid'],
                'cid': cid,
                'roles': composer.xpath('.//span[contains(@class,"roles")]/text()').get()
            }
            yield CopyrightItem(copyright)
            request = Request(compose_url % cid, callback=self.parse_composer)
            request.meta['cid'] = cid
            yield request

            comment_api = "http://www.xinpianchang.com/article/filmplay/ts-getCommentApi?id=%s&page=1"
            yield response.follow(comment_api % post['pid'], callback=self.parse_comment)

    # 评论,ajax
    def parse_comment(self, response):
        result = json.loads(response.text)
        comments = result['data']['list']
        for c in comments:
            comment = CommentItem()
            comment['commentid'] = c['commentid']
            comment['pid'] = c['articleid']
            comment['cid'] = c['userInfo']['userid']
            comment['avatar'] = c['userInfo']['face']
            comment['uname'] = c['userInfo']['username']
            comment['created_at'] = c['addtime']
            comment['content'] = c['content']
            comment['like_counts'] = c['count_approve'].replace(',', '')
            if c['reply']:
                comment['reply'] = c['reply']['commentid']
            yield comment

        next_page = result['data']['next_page_url']
        if next_page:
            yield response.follow(next_page)

    # 导演详情页
    def parse_composer(self, response):
        composer = ComposerItem()
        composer['cid'] = response.meta['cid']
        composer['name'] = response.xpath('//p[contains(@class,"creator-name")]/text()').get()
        composer['banner'] = response.xpath('//div[@class="banner-wrap"]/@style').get()[21:-1]
        composer['avatar'] = response.xpath('//span[@class="avator-wrap-s"]/img/@src').get()
        v = response.xpath('//span[@class="author-v yellow-v"]')
        composer['verified'] = 1 if v else 0
        composer['intro'] = response.xpath('//p[contains(@class,"creator-desc")]/text()').get()
        composer['like_counts'] = response.xpath('//span[contains(@class,"like-counts")]/text()').get().replace(',', '')
        composer['fans_counts'] = response.xpath('//span[contains(@class,"fans-counts")]/text()').get().replace(',', '')
        composer['follow_counts'] = response.xpath(
            '//span[@class="follow-wrap"]/span[contains(@class,"fw")]/text()').get().replace(',', '')
        composer['location'] = response.xpath('//p[contains(@class,"creator-detail")]/span[5]/text()').get()
        composer['career'] = response.xpath('//p[contains(@class,"creator-detail")]/span[last()]/text()').get()
        yield composer
