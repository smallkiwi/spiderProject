import time
from selenium import webdriver
import lxml.etree
import signal
import re
import requests
import redis
import threading

threads = []
DOWNLOADER_NUM = 10  # 线程数量
myredis = redis.Redis(host='10.36.131.167',port=6379,password="root")  # 开启数据库
thread_on = True
DOWNLOAD_DELAY = 0.3  # 下载延迟

# 获取session
session = requests.session()
for i in session.cookies:
    print(i.name, i.value)


def write():
    global session
    loginUrl = 'https://accounts.douban.com/login'
    # 模拟浏览器
    driver = webdriver.Chrome()
    driver.get(loginUrl)
    # 验证码
    driver.find_element_by_name("form_email").send_keys("707739450@qq.com")
    driver.find_element_by_name("form_password").send_keys("123456mai")
    time.sleep(10)
    # 模拟点击
    driver.find_element_by_xpath('//input[contains(@class,"btn-submit")]').click()
    time.sleep(2)
    session = requests.session()
    for i in session.cookies:
        print(i.name, i.value)
    # 作者连接爬取
    while True:
        # 每一页的作者链接
        pagesource = lxml.etree.HTML(driver.page_source)
        post_link = pagesource.xpath('//*[@class="stream-items"]//div[@class="title"]/a/@href')
        # 存储链接
        for link in post_link:
            if myredis.sadd('douban.seen', link):  # 保存所有爬过的历史信息,如果插入成功说明链接没有爬过,则压入要爬取的队列中
                myredis.lpush('douban.queue', link)

        if len(post_link) == 0:
            break
        # 翻页
        next_page = driver.find_element_by_xpath('//div[contains(@class,"paginator")]/span[last()]/a')
        if next_page:
            next_page.click()
        else:
            break
        # 等待3秒
        time.sleep(3)
    driver.quit()


def read(num):
    print('Thread-%s' % num)
    global session
    while thread_on:
        # 遵循先进先出的原则,左边压入,右边弹出
        post_link = myredis.rpop('douban.queue')
        for i in session.cookies:
            print(i.name, i.value)
        if post_link:
            pagesource = session.get(post_link).text
            # lxml解析
            pagecontent = lxml.etree.HTML(pagesource)
            regex = re.compile(r'(\d+)')
            pid = regex.findall(post_link.decode('utf-8'))
            title = pagecontent.xpath('//div[contains(@class,"note-header")]/h1/text()')
            author = pagecontent.xpath('//div[contains(@class,"note-header")]//a[@class="note-author"]/text()')
            date = pagecontent.xpath('//div[contains(@class,"note-header")]//span[@class="pub-date"]/text()')
            passage = pagecontent.xpath('//div[@id="link-report"]//p//text()')
            post = ''.join(passage)
            if len(pid) != 0 and len(title) != 0 and len(author) != 0 and len(date) != 0 and len(passage) != 0:
                data = {
                    'pid': pid[0],
                    'title': title[0],
                    'author': author[0],
                    'date': date[0],
                    'passage': post
                }
                myredis.lpush('douban.items', data)
            time.sleep(3)
    time.sleep(DOWNLOAD_DELAY)
    print('Thread-%s exit now.' % i)

# 信号量
def sigint_handler(signum, frame):
    print('Received Ctrl+C, wait for exit gracefully')
    global thread_on
    thread_on = False


if __name__ == '__main__':
    start_time = time.time()
    write()  # 获取链接队列
    for num in range(DOWNLOADER_NUM):
        t = threading.Thread(target=read, args=(num + 1,))
        t.start()
        threads.append(t)

    signal.signal(signal.SIGINT, sigint_handler)

    for t in threads:
        t.join()
    cost_time = time.time() - start_time
    print('cost %s seconds' % cost_time)
