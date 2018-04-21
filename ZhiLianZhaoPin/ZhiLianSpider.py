import re
import requests
import urllib.request
import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
from multiprocessing import Pool

# 开启数据库
cn = MongoClient('localhost', 27017)
db = cn.job
table = db.zhilian
# 初始化数据库
table.remove({})

# 初始化测试数据
job = 'python'
place = '深圳'
job_url = urllib.request.quote(job.encode('utf-8'))
place_url = urllib.request.quote(place.encode('utf-8'))


# 获取页数
def get_page():
    url = 'https://sou.zhaopin.com/jobs/searchresult.ashx?jl={}&kw={}&sm=0&p=1'.format(place_url, job_url)
    wbdata = requests.get(url).content
    soup = BeautifulSoup(wbdata, 'lxml')
    items = soup.select('table[class="newlist"]')
    count = len(items) - 1
    # 每页职位信息数量
    print('每个页面的有%s条数据' % count)
    job_count_data = soup.find('span', class_="search_yx_tj")
    job_count = re.search(r'\d{1,}', job_count_data.get_text()).group()

    print('满足搜索条件职位有%s个' % job_count)
    # 搜索结果页数
    pages = (int(job_count) / count) + 1
    print('一共有%d页面' % pages)
    return pages


# 主程序
def get_zhaopin(page_):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
    url = 'https://sou.zhaopin.com/jobs/searchresult.ashx?jl={}&kw={}&sm=0&p={}'.format(place_url, job_url, page_)

    wbdata = requests.get(url, headers=headers).content
    soup = BeautifulSoup(wbdata, 'lxml')
    job_name = soup.select("table.newlist > tr > td.zwmc > div > a:nth-of-type(1)")
    companys = soup.select("table.newlist > tr > td.gsmc > a:nth-of-type(1)")
    salarys = soup.select("table.newlist > tr > td.zwyx")
    locations = soup.select("table.newlist > tr > td.gzdd")
    times = soup.select("table.newlist > tr > td.gxsj > span")

    for name, company, salary, location, time in zip(job_name, companys, salarys, locations, times):
        data = {
            'name': name.get_text(),
            'company': company.get_text(),
            'salary': salary.get_text(),
            'location': location.get_text(),
            'time': time.get_text(),
        }
        table.insert_one(data)


# 开启5进程,进程池
if __name__ == "__main__":
    page = get_page()
    start_time = datetime.datetime.now()
    pool = Pool(processes=5)  # 最大进程数
    pool.map_async(get_zhaopin, range(1, int(page) + 1))
    pool.close()
    pool.join()
    end_time = datetime.datetime.now()
    print('花费总时间为：%sS' % (end_time - start_time).seconds)
