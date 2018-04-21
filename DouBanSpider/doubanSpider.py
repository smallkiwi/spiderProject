from selenium import webdriver
import lxml.etree
import time
from multiprocessing import Process, Queue
import re
from pymongo import MongoClient
import requests

session = requests.session()
for i in session.cookies:
    print(i.name,i.value)
# print(session)

# 开启数据库
cn = MongoClient('localhost', 27017)
db = cn.douban
table = db.post
# 初始化数据库
table.remove({})

def write(q):
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
        for link in post_link:
            q.put(link)
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


def read(q):
    global session
    while True:
        post_link = q.get()
        # 请求头
        # opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie))
        # urllib.request.install_opener(opener)
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3236.0 Safari/537.36'}
        # requests = urllib.request.Request(url=post_link, headers=headers)
        # pagesource = urllib.request.urlopen(requests).read()
        for i in session.cookies:
            print(i.name, i.value)
        pagesource = session.get(post_link).text
        # lxml解析
        pagecontent = lxml.etree.HTML(pagesource)
        regex = re.compile(r'(\d+)')
        pid = regex.findall(post_link)
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
            table.insert_one(data)
        time.sleep(3)


if __name__ == '__main__':
    # 主进程创建Queue,并作为参数传递给子进程
    q = Queue()
    pw = Process(target=write, args=(q,))
    pr = Process(target=read, args=(q,))
    # 启动子进程pw,往Queue中写入
    pw.start()
    # 启动子进程pr,从Queue中读取
    pr.start()
    # 等待写进程执行结束
    pw.join()
    # 终止读取进程
    pr.terminate()
