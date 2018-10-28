# 无法提取的网页
# http://www.mohrss.gov.cn/gkml/index3.html
from app import UserInfo

__author__ = 'tian'

import scrapy
import logging
import time
from lxml import etree
from scrapy_splash import SplashRequest
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.expected_conditions import staleness_of

import redis
from app.setting import *
from contextlib import contextmanager
# from app.views import getWebsite
# from app.views import getlistxpath
# from app.views import getpage
# from app.views import get_input_xpath
from scrapyTool.ScrapyTool.spiders.toolSpider import ToolSpider
from scrapyTool.ScrapyTool.spiders.toolSpider import first_script
from scrapyTool.ScrapyTool.spiders.toolSpider import script

# class wait_for_page_load(object):
#     def __init__(self, browser):
#         self.browser = browser
#
#     def __enter__(self):
#         print('class1')
#         self.old_page = self.browser.find_element_by_tag_name('html')
#
#     def page_has_loaded(self):
#         print('class2')
#         new_page = self.browser.find_element_by_tag_name('html')
#         return new_page.id != self.old_page.id
#
#     def wait_for(condition_function):
#         print('class3')
#         start_time = time.time()
#         while time.time() < start_time + 3:
#             if condition_function():
#                 return True
#             else:
#                 time.sleep(0.1)
#         raise Exception(
#             'Timeout waiting for {}'.format(condition_function.__name__)
#         )
#
#     def __exit__(self, *_):
#         print('class4')
#         self.wait_for(self.page_has_loaded)


class SeleniumSpider(ToolSpider):
    name = "selenium"

    def __init__(self, id='', **kwargs):
        super(SeleniumSpider, self).__init__(id, **kwargs)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        # self.browser = webdriver.Chrome(chrome_options = chrome_options)
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 20)
        self.r = redis.StrictRedis(host=RHOST, port=RPORT)
        self.userinfo = UserInfo.from_json(self.r.get(self.aid))
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # self.logger = logging.getLogger('tian')
        print("---SeleniumSpider---")
        self.pagenum = ""
        if self.userinfo['selenium_page']:
            self.pagenum = int(self.userinfo['selenium_page'])
        self.input_xpath = self.userinfo['page_num_xpath_list']
        logging.info('页码所在的xpath:%s'%self.input_xpath)
        self.flag = None
        print(self.input_xpath, self.flag)
        print('__init__ends')

    def __del__(self):
        self.browser.close()

    def start_requests(self):
        website = self.userinfo['website']

        yield scrapy.Request(url=website, callback=self.parse, meta={'url': website})

    @contextmanager
    def wait_for_page_load(self, timeout=12):
        old_page = self.browser.find_element_by_tag_name('html')
        yield
        WebDriverWait(self.browser, timeout).until(
            staleness_of(old_page)
        )

    def parse(self, response):
        # print('text:', response.text)
        parse_url = response.meta['url']
        list_a = self.userinfo['url_list_xpath']
        self.browser.get(parse_url)
        # 接收到xpath则用xpath解析列表
        # //div[@class="m2"]/ul//h3
        if list_a:
            urls = None
            i = 1
            while True:
                url_list = []
                try:
                    html = self.browser.page_source
                    doc = etree.HTML(html)
                    # print("doc",html)
                    if urls == doc.xpath(list_a + '//a/@href'):
                        print('已经到最后一页')
                        self.browser.close()
                        break
                    urls = doc.xpath(list_a + '//a/@href')

                    if not urls:
                        logging.info('the xpath is incorrect')
                    else:
                        logging.debug('urls: %s' % urls)
                    for _url in urls:
                        _url = response.urljoin(_url)
                        url_list.append(_url)
                    for _u in url_list:
                        yield SplashRequest(url=_u, callback=self.con_parse, endpoint='execute',
                                            args={'lua_source': first_script, 'wait': 3, 'NEXTPAGE_KEYWORD': 'next',
                                                  'page': 1})
                    print('pause for a moment')
                    time.sleep(3)
                    if self.pagenum and i < self.pagenum:
                        i = i + 1
                        print("i is", i)

                    if not self.flag:
                        try:
                            _next = self.wait.until(EC.element_to_be_clickable(
                                (By.XPATH, '//a[contains(text(), "下页") or contains(text(), "下一页")]')))
                            _next.click()
                        except Exception as e:
                            logging.debug('the error is %s'%e)
                            try:
                                input = self.wait.until(
                                    EC.presence_of_element_located((By.XPATH, self.input_xpath + "//input[@type='text']")))
                                # logging('input:%s'%input)
                                input.clear()
                                input.send_keys(str(i))
                                # with self.wait_for_page_load(timeout=10):
                                input.send_keys(Keys.ENTER)  # 回车键(ENTER)
                                self.flag = 1
                            except Exception as e:
                                logging.debug('again the error is %s' % e)
                                logging.debug("没找到方框")
                                try:
                                    btnclick = self.wait.until(EC.element_to_be_clickable(
                                        (By.XPATH, self.input_xpath + "/a[{}]".format(i-1))))
                                    btnclick.click()
                                    self.flag = 2
                                except TimeoutException:
                                    logging.debug("无法点击")
                    elif self.flag == 1:
                        # with wait_for_page_load(self.browser):
                        input = self.wait.until(
                            EC.presence_of_element_located((By.XPATH, self.input_xpath + "//input[@type='text']")))
                        input.clear()

                        input.send_keys(str(i))

                        print('qqqqqqqqq')
                        # with self.wait_for_page_load(timeout=10):
                        input.send_keys(Keys.ENTER)  # 回车键(ENTER)
                        print('ppppppppp')
                    else:
                        btnclick = self.wait.until(
                            EC.element_to_be_clickable(
                                (By.XPATH, self.input_xpath + '/a[{}]'.format(i))))

                        btnclick.click()
                    time.sleep(2)
                except Exception as e:
                    logging.info(e)

        else:
            # 可能需要完善这个列表自动识别算法
            print("列表自动识别")
            urls = response.xpath('//a')
            myUrls = []
            for url in urls:
                url_ = url.xpath('./@href').extract_first()
                if url_ is not None:
                    if 'javascript' not in url_:
                        # print('url_',url_)
                        myUrls.append(url_)
            totalSubgroup, mylen = self.getListClusterByXpath(urls)
            text_longest_index = mylen.index(max(mylen))  # 最大长度对应的索引
            text_second_index = mylen.index(sorted(mylen)[-2])
            list_longest = len(totalSubgroup[text_longest_index])  # 个数
            list_second = len(totalSubgroup[text_second_index])
            if mylen[text_longest_index] * 1.0 / list_longest < mylen[
                text_second_index] * 1.0 / list_second and list_second >= 10:
                myresult = totalSubgroup[text_second_index]
                print('super')
            # print('myresult,',totalSubgroup[mylen.index(max(mylen))])
            else:
                myresult = totalSubgroup[mylen.index(max(mylen))]
            for tsg in myresult:
                print('tsg,', tsg.xpath('./@href').extract_first())
            final_urls = [tsg.xpath('./@href').extract_first() for tsg in myresult]

            for url_alis in final_urls:
                # print('the link is %s' % url_alis)
                url_alis = response.urljoin(url_alis)
                if not url_alis in self.bloom:
                    yield scrapy.Request(url=url_alis, callback=self.con_parse)
                else:
                    print('已经爬取过了')

            url = response.data['url_']
            yield SplashRequest(url, callback=self.parse, endpoint='execute',
                                args={'lua_source': script, 'wait': 3, 'NEXTPAGE_KEYWORD': 'next', 'page': 1})