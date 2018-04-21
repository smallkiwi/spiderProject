import time
import requests
import lxml.etree
import redis
import pymysql
from multiprocessing import Process

myredis = redis.Redis(host='10.36.131.167', port=6379)  # 开启redis数据库
sqldb = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='root', db='dianping', charset='utf8')
cursor = sqldb.cursor()  # 开启mysql数据库

start_url = "http://www.dianping.com/shenzhen/ch10"  # 起始网址
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3236.0 Safari/537.36"
}


def get_url():
    # 获取组合网址
    pagesource = requests.get(start_url, headers=headers).text
    pagetree = lxml.etree.HTML(pagesource)
    classfy = pagetree.xpath('//div[@id="classfy"]/a/@data-cat-id')
    place = []
    bussi_nav = pagetree.xpath('//div[@id="bussi-nav"]/a/@data-cat-id')
    place.extend(bussi_nav)
    region_nav = pagetree.xpath('//div[@id="region-nav"]/a/@data-cat-id')
    place.extend(region_nav)
    metro_nav = pagetree.xpath('//div[@id="metro-nav"]/a/@data-cat-id')
    place.extend(metro_nav)
    url_list = []
    for category in classfy:
        for site in place:
            combine_url = "http://www.dianping.com/shenzhen/ch10/g{}r{}".format(category, site)
            url_list.append(combine_url)
    return url_list


# 网址存入redis数据库
def get_pagination(url_list):
    # 获取组合后的分页
    for url in url_list:
        pagesource = requests.get(url, headers=headers).text
        pagetree = lxml.etree.HTML(pagesource)
        pages = pagetree.xpath('//div[@class="page"]/a/@data-ga-page')
        if len(pages) != 0:
            pg = int(pages[len(pages) - 2])
            for p in range(1, pg + 1):
                new_url = url + 'p' + str(p)
                if myredis.sadd('dianping.seen', new_url):  # 保存所有爬过的历史链接
                    myredis.lpush('dianping.queue', new_url)  # 待爬取链接队列
        else:
            if myredis.sadd('dianping.seen', new_url):
                myredis.lpush('dianping.queue', new_url)
        time.sleep(3)


# 从redis中获取网址,解析后数据存入mysql
def shop_parse():
    while True:
        # 遵循先进先出的原则,左边压入,右边弹出
        url = myredis.rpop('dianping.queue')
        if url:
            pagesource = requests.get(url, headers=headers).text
            selector = lxml.etree.HTML(pagesource)
            div = selector.xpath('//div[@id="shop-all-list"]/ul/li')
            for dd in div:
                # 商店名
                shopname = dd.xpath('./div[contains(@class,"txt")]/div[contains(@class,"tit")]//h4/text()')[0]
                # 商店url
                shopurl = dd.xpath('./div[contains(@class,"txt")]/div[contains(@class,"tit")]/a/@href')[0]
                # 商店星级
                shoplevel = dd.xpath('.//div[contains(@class,"comment")]/span/@title')[0]
                # 评论数
                commentnums = dd.xpath('.//div[contains(@class,"comment")]/a[contains(@class,"review-num")]/b/text()')
                if len(commentnums) > 0:
                    commentnums = commentnums[0]
                else:
                    commentnums = '0'
                # 人均价格
                avgcosts = dd.xpath('.//div[contains(@class,"comment")]/a[contains(@class,"mean-price")]/b/text()')
                if len(avgcosts) > 0:
                    avgcosts = ''.join(list(filter(str.isdigit, str(avgcosts[0]))))  # 函数式编程
                else:
                    avgcosts = '0'
                # 口味评分
                taste_score = dd.xpath('.//span[contains(@class,"comment-list")]/span[1]/b/text()')
                if len(taste_score) > 0:
                    taste_score = taste_score[0]
                else:
                    taste_score = '0'
                # 环境评分
                envis_score = dd.xpath('.//span[contains(@class,"comment-list")]/span[2]/b/text()')
                if len(envis_score) > 0:
                    envis_score = envis_score[0]
                else:
                    envis_score = '0'
                # 服务评分
                service_score = dd.xpath('.//span[contains(@class,"comment-list")]/span[3]/b/text()')
                if len(service_score) > 0:
                    service_score = service_score[0]
                else:
                    service_score = '0'
                # 分类
                foodtype = dd.xpath('.//div[@class="tag-addr"]/a[1]/span/text()')
                if len(foodtype) > 0:
                    foodtype = foodtype[0]
                else:
                    foodtype = '暂无分类'
                # 地点
                locs = dd.xpath('.//div[@class="tag-addr"]/a[2]/span/text()')
                if len(locs) > 0:
                    locs = locs[0]
                else:
                    locs = '地点不明'
                print(shopname, shopurl, shoplevel, commentnums, avgcosts, taste_score, envis_score, service_score,
                      foodtype, locs)
                cursor.execute(
                    "INSERT INTO shopinfo(shopname,shopurl,shoplevel,commentnums,avgcosts,taste_score,envis_score,service_score,foodtype,locs)VALUES('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}','{9}');".format(
                        pymysql.escape_string(shopname), shopurl, shoplevel, commentnums, avgcosts, taste_score,
                        envis_score, service_score,
                        foodtype, locs))
                sqldb.commit()
        time.sleep(3)
    cursor.close()
    sqldb.close()


if __name__ == '__main__':
    url_list = get_url()
    pg = Process(target=get_pagination, args=(url_list,))
    sp = Process(target=shop_parse)
    # 启动子进程pg,往redis的queue中写入
    pg.start()
    # 启动子进程sp,从Queue中读取链接并解析网页
    sp.start()
    # 等待写进程执行结束
    pg.join()
    # 终止解析进程
    sp.terminate()
