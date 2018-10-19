import scrapy
import time
from lxml import etree
from scrapy_splash import SplashRequest
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys

from app.views import getWebsite
from app.views import getlistxpath
from app.views import getpage
from app.views import get_input_xpath
from scrapyTool.ScrapyTool.spiders.toolSpider import ToolSpider
from scrapyTool.ScrapyTool.spiders.toolSpider import first_script
from scrapyTool.ScrapyTool.spiders.toolSpider import script

import logging


class SeleniumSpider(ToolSpider):
    name = "selenium"

    def __init__(self, id='', **kwargs):
        super(SeleniumSpider, self).__init__(id, **kwargs)
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        # chrome_options = chrome_options
        self.browser = webdriver.Chrome(chrome_options=chrome_options)
        self.wait = WebDriverWait(self.browser, 20)
        # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        print("---SeleniumSpider---")
        self.pagenum = 0
        if getpage():
            self.pagenum = int(getpage())
            print("self num", self.pagenum)
        self.input_xpath = get_input_xpath()
        self.flag = None

    def __del__(self):
        self.browser.close()

    def start_requests(self):
        website = getWebsite()

        yield scrapy.Request(url=website, callback=self.parse, meta={'url': website})

    def parse(self, response):
        parse_url = response.meta['url']
        list_a = getlistxpath()
        self.browser.get(parse_url)
        # 接收到xpath则用xpath解析列表
        # //div[@class="m2"]/ul//h3
        if list_a:
            urls = None
            num = 1
            while True:
                url_list = []
                try:
                    html = self.browser.page_source
                    doc = etree.HTML(html)
                    if urls == doc.xpath(list_a + '//a/@href'):
                        logging.info('已经到最后一页')
                        self.browser.close()
                        break
                    urls = doc.xpath(list_a + '//a/@href')

                    logging.info('urls:', urls)
                    if not urls:
                        logging.info('the xpath is incorrect')
                    for _url in urls:
                        _url = response.urljoin(_url)
                        url_list.append(_url)
                    for _u in url_list:
                        yield SplashRequest(url=_u, callback=self.con_parse, endpoint='execute',
                                            args={'lua_source': first_script, 'wait': 3, 'NEXTPAGE_KEYWORD': 'next',
                                                  'page': 1})
                    print('pause for a moment')
                    time.sleep(3)
                    if self.pagenum and num < self.pagenum:
                        num = num + 1

                    if not self.flag:
                        s = ["下一页", "下页", ">"]
                        try:
                            next = self.wait.until(EC.element_to_be_clickable(
                                (By.XPATH, '//*[contains(text(), "下页") or contains(text(), "下一页")]')))
                            next.click()
                        except TimeoutException:
                            try:
                                input = self.wait.until(EC.presence_of_element_located(
                                    (By.XPATH, self.input_xpath + '//input[@type="text"]')))
                                input.clear()
                                input.send_keys(str(i))
                                input.send_keys(Keys.ENTER)  # 回车键(ENTER)
                                self.flag = 1
                            except TimeoutException:
                                logging.debug("没找到方框")
                                try:
                                    btnclick = self.wait.until(EC.element_to_be_clickable(
                                        (By.XPATH, self.input_xpath + '//a[text()=str(num)]')))
                                    btnclick.click()
                                    self.flag = 2
                    elif self.flag == 1:
                        input = self.wait.until(EC.presence_of_element_located((By.XPATH, self.input_xpath)))
                        input.clear()
                        input.send_keys(str(num))
                        input.send_keys(Keys.ENTER)  # 回车键(ENTER)
                    else:
                        btnclick = self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, self.input_xpath + '//a[text()=str(num)]')))
                        btnclick.click()
                    time.sleep(1)
                except Exception as e:
                    logging.info(e)

        else:
            # 可能需要完善这个列表自动识别算法
            logging.debug("列表自动识别")
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
            print('myresult,', totalSubgroup[mylen.index(max(mylen))])
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
                logging.debug('已经爬取过了')

        url = response.data['url_']
        yield SplashRequest(url, callback=self.parse, endpoint='execute',
                            args={'lua_source': script, 'wait': 3, 'NEXTPAGE_KEYWORD': 'next', 'page': 1})
