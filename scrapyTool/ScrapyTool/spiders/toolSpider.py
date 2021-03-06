from scrapy.exceptions import CloseSpider
import re,logging
import scrapy
import pymysql
import redis
from app.setting import *
from scrapy_splash import SplashRequest

# from app.views import getScrapyList
# from app.views import getWebsite
# from app.views import getCurType
# from app.views import getDefaultFlag
# from app.views import getlistxpath
from app.User import UserInfo

from scrapyTool.ScrapyTool.items import MyItem
from scrapyTool.ScrapyTool.AticleWithAttachment import ArticleWithAttachment
from scrapyTool.ScrapyTool.Title import Title
from bloom_filter import BloomFilter

script = """
function main(splash, args)
  splash:autoload("https://code.jquery.com/jquery-2.1.3.min.js")
  splash:go(args.url)
  local get_a=splash:jsfunc([[
    function test(){
        var flag = false
        var _items = document.getElementsByTagName('a');
        var i = 0

        for(i =0;i<_items.length;i++)
        {
            if(_items[i].innerText == '下一页' || _items[i].innerText =='下页' || _items[i].innerText =='>')
            {
                    _items[i].click();
                    break;

            }
        }
    }
 ]])
  get_a()

  splash:wait(2)
  return {html=splash:html(), url_ = splash:url()}
end
"""
first_script = """
function main(splash, args)
  splash:go(args.url)

  splash:wait(2)
  return {html=splash:html(),url_ = splash:url()}
end
"""


logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                     filename='new.log',
                     filemode='a',  ##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                     # a是追加模式，默认如果不写的话，就是追加模式
                     format=
                     '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                     # 日志格式
                     )


class ToolSpider(scrapy.Spider):
    name = "Tool"

    def __init__(self, id='', **kwargs):
        super(ToolSpider, self).__init__(**kwargs)
        self.conn = pymysql.connect(host=HOST, user=USER, passwd=PASSWD, db=DB, charset='utf8', port=PORT)
        self.r = redis.StrictRedis(host=RHOST, port=RPORT)
        self.cursor = self.conn.cursor()
        self.aid = id
        self.click_button_flag = False
        self.bloom = BloomFilter(max_elements=100000, error_rate=0.05)
        self.userinfo = UserInfo.from_json(self.r.get(self.aid))
        self._getWebsitesInDB()

    def _getWebsitesInDB(self):
        table_name = self.userinfo['table_name']
        logging.debug("[spider]current table name is : %s"%table_name)
        table_url = table_name[table_name.rindex('_') + 1:] + '_url'
        # print('table_url',table_url)
        sql = 'select {} from %s'.format(table_url) % table_name
        # print('sql',sql)
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        if results is not None:
            for r in results:
                self.bloom.add(r[0])

    def start_requests(self):
        print('start_requests')
        website = self.userinfo['website']
        yield SplashRequest(url=website, callback=self.parse, endpoint='execute',
                            args={'lua_source': first_script, 'wait': 3, 'NEXTPAGE_KEYWORD': 'next', 'page': 1})

    def parse(self, response):
        # list_a = self.userinfo['url_list_xpath']
        # # 接收到xpath则用xpath解析列表
        # # //div[@class="m2"]/ul//h3
        # if list_a:
        #     list_href = list_a + '//a/@href'
        #     list_urls = response.xpath(list_href).extract()
        #     list_urls = list(set(list_urls))
        #     final_urls = list_urls[:]
        #     for url in list_urls:
        #         if url == '#' or "javascript" in url:
        #             final_urls.remove(url)
        #     print("final_urls", len(final_urls))
        list_a = self.userinfo['url_list_xpath']
        if list_a:
            final_urls = list()
            child_nodes = response.xpath(list_a + '/child::*')
            for child_node in child_nodes:
                a_nodes = child_node.xpath('.//a')
                max_len = 0
                max_node = None
                for a_node in a_nodes:
                    text = a_node.xpath('.//text()').extract_first()
                    if text:
                        if len(text) > max_len:
                            max_len = len(text)
                            max_node = a_node

                final_urls.append(max_node.xpath('./@href').extract_first())
            final_urls = list(set(final_urls))
            backup_urls = final_urls[:]

            if list_a in self.userinfo['page_num_xpath_list']:
                # urls = doc.xpath(list_a + '//a/@href')
                num_urls = response.xpath(self.userinfo['page_num_xpath_list'] + '//a/@href')
                for temp_url in backup_urls:
                    if temp_url in num_urls:
                        final_urls.remove(temp_url)
            for temp_url in backup_urls:
                if '#' == temp_url or "javascript" in temp_url:
                    final_urls.remove(temp_url)
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
            url_alis = response.urljoin(url_alis)
            if not url_alis in self.bloom:
                yield scrapy.Request(url=url_alis, callback=self.con_parse)
            else:
                print('已经爬取过了')

        url = response.data['url_']
        yield SplashRequest(url, callback=self.parse, endpoint='execute',
                            args={'lua_source': script, 'wait': 3, 'NEXTPAGE_KEYWORD': 'next', 'page': 1})

    def con_parse(self, response):
        # print('userinfo in con_parse:',self.userinfo)
        default_flag = self.userinfo['default_crawl_flag']
        xpathList = []
        combination = []
        item = MyItem()
        table_name = self.userinfo['table_name']
        finalFlag = self.myPipeline.getFlag()
        if finalFlag:
            if finalFlag == 'nosw':
                # self.r.delete(self.aid)
                self.click_button_flag = True
                logging.info('con_parse closed')
                self.userinfo['if_store_data'] = 'start'
                self.userinfo['crawling_result'] = {}
                # self.userinfo['spider_state'] = 'close'
                self.r.set(self.aid, self.userinfo.to_json())
                raise CloseSpider('用户不想继续爬取nosw')
            if finalFlag == 'no':
                self.click_button_flag = True
                self.userinfo['if_store_data'] = 'no'
                self.userinfo['crawling_result'] = {}
                self.userinfo['spider_state'] = 'close'
                self.userinfo['error_msg'] = '爬虫程序已经关闭'
                self.r.set(self.aid, self.userinfo.to_json())
                raise CloseSpider('用户不想继续爬取no')


        if default_flag == 1:
            print('---default crawl---')
            mytitle,myarticle = self.getTitleAndText(response)

            # 时间
            reBODY = re.compile(r'<body.*?>([\s\S]*?)</body>', re.I)
            reDate = re.compile(r'时间|发布日期|发文日期|发布时间|日期', re.S)
            Hbody = None
            date = None
            if re.findall(reBODY, response.text):
                Hbody = re.findall(reBODY, response.text)[0]
            timeTag = response.xpath('//*[contains(text(),"发布日期")] /../..// text()').extract()
            if not timeTag:
                timeTag = response.xpath('//*[contains(text(),"发布时间")] /../..// text()').extract()
            if timeTag:
                timeStr = "".join(timeTag).replace("\n", "").replace("\r", "").replace("\t", "")
                # resultStr = re.sub('\s', '', timeStr)
                date = re.search('\d{4}.\d{2}.\d{2}.', timeStr)
            else:
                if Hbody:
                    date = re.search('\d{4}[^0-9]\d{2}[^0-9]\d{2}', Hbody)


            if SETTING_FOR_GUOCE:
                table_title = table_name[table_name.rindex('_') + 1:] + 'title'
                table_publish_time = table_name[table_name.rindex('_') + 1:] + '_publish_time'
                table_text = table_name[table_name.rindex('_') + 1:] + '_text'
                table_url = table_name[table_name.rindex('_') + 1:] + '_url'
                item[table_title] = mytitle
                item[table_text] = myarticle
                if date:
                    item[table_publish_time] = date.group()
                else:
                    item[table_publish_time] = ""
                item[table_url] = response.url
                yield item
            else:
                sql_order = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}'".format(
                    table_name)
                self.cursor.execute(sql_order)
                fields_result = self.cursor.fetchall()
                for field_result in fields_result:
                    if 'title' in field_result:
                        item[field_result] = mytitle
                    if 'text' in field_result:
                        item[field_result] = myarticle
                    if 'url' in field_result:
                        item[field_result] = response.url
                    # TODO关于时间字段，可能存在问题
                    if date:
                        if 'time' in field_result:
                            item[field_result] = date
                yield item


        # 非默认爬取功能
        else:


            logging.debug('---crawl start---')
            scrapyList = self.userinfo['fields_xpath_list']
            sql_order = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}'".format(table_name)
            cursor = self.conn.cursor()
            cursor.execute(sql_order)
            result = cursor.fetchall()

            # 得到前台页面显示的字段
            data_show = []
            for k in DISPLAY.keys():
                for kt in result:
                    if k in kt[0]:
                        data_show.append(kt[0])
                        break
            #这里有点问题
            # table_url = table_name[table_name.rindex('_') + 1:] + '_url'
            for r in result:
                xpathList.append(r[0])

            for i in zip(scrapyList, data_show):
                if i[0] and i[1]:
                    combination.append(list(i))

            # 标题的字段名必须含有'title',正文的字段必须含有'text'
            if SETTING_FOR_GUOCE:
                #取标题最后4位来判断文体
                def getStyle(text):
                    styleTuple = ('通知','公告','报告','意见','办法','通报','决定','批复','其他')
                    if '_' in text:
                        text = text.split('_')[0]
                    _text = text[-4:]
                    for i,st in enumerate(styleTuple):
                        if st in _text:
                            return i+1
                    return len(styleTuple)

                table_url = table_name[table_name.rindex('_') + 1:] + '_url'
                mytitle, myarticle = self.getTitleAndText(response)
                for res in result:
                    if 'title' in res[0]:
                        item[res[0]] = mytitle
                    if 'text' in res[0]:
                        item[res[0]] = myarticle
                    if 'style' in res[0]:
                        item[res[0]] = getStyle(mytitle)

                item[table_url] = response.url


            for c in combination:
                xpath_profix = c[0][c[0].rindex('/')+1:]
                # print('xpath_profix:',xpath_profix)
                if self.judgeXpathFromText(c[0]):
                    if 'meta' in xpath_profix:
                        print('meta in xpath')
                        c[0] = c[0] + '/@content'
                    else:
                        c[0] = c[0] + '/text()'

                    _xpath_result = response.xpath(c[0]).extract_first()
                    #判断长度小于30且含有日期格式时，将其保存为data格式，方便存入数据库中
                    if _xpath_result:
                        if len(_xpath_result.strip()) < 30 and self.extractDate(_xpath_result) is not None:
                            _xpath_result = self.extractDate(_xpath_result)

                    item[c[1]] = _xpath_result
                else:
                    #允许用户输入文本作为内容
                    item[c[1]] = c[0]
                # print(item)
            # item[table_url] = response.url
            for res in result:
                if 'url' in res[0]:
                    item[res[0]] = response.url
            yield item

    def close(spider, reason):
        logging.info('spider关闭了')
        userinfo = UserInfo.from_json(spider.r.get(spider.aid))
        #由于closespider关闭需要时间,所以应该区分自然关闭还是强制关闭
        if not spider.click_button_flag:
            userinfo['spider_state'] = 'nature_close'
            userinfo['error_msg'] = '爬虫程序已经关闭'
        else:
            userinfo['spider_state'] = 'close'
        # userinfo['spider_state'] = 'close'

        spider.r.set(spider.aid, userinfo.to_json())
        logging.info('aha,the spider closed')




    def levenshteinDistance(self, s1, s2):
        if len(s1) > len(s2):
            s1, s2 = s2, s1
        distances = range(len(s1) + 1)
        for i2, c2 in enumerate(s2):
            distances_ = [i2 + 1]
            for i1, c1 in enumerate(s1):
                if c1 == c2:
                    distances_.append(distances[i1])
                else:
                    distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
            distances = distances_
        return distances[-1]

    def getSplitList(self, myList):
        mySplitList = []
        for m in myList:
            my_ = []
            my_ = m.split('/')
            my_ = [m for m in my_ if m != '']
            mySplitList.append(my_)
        return mySplitList

    def getListClusteringByEditDistance(self, myList):
        pass

    def getListClusterByXpath(self, myList):
        gap = []
        if myList:
            for i in range(len(myList) - 1):
                thegap = self.belongToTheSame(myList[i], myList[i + 1])
                if thegap == 5:
                    textResult = self.judgeFromAncestor(myList[i], myList[i + 1])
                    if textResult:
                        thegap = 1
                gap.append(thegap)
        subgroup = []
        totalSubgroup = []
        subgroup_len = 0
        subgroup_len_list = []
        length_list = []
        length_ = 0
        for lg in range(len(gap)):
            if gap[lg] != 5 and lg < len(gap) - 1:
                subgroup_len += len(myList[lg].xpath('string(.)').extract_first())
                subgroup.append(myList[lg])
            if gap[lg] == 5 or lg == len(gap) - 1:
                subgroup_len += len(myList[lg].xpath('string(.)').extract_first())
                subgroup_len_list.append(subgroup_len)
                subgroup.append(myList[lg])
                totalSubgroup.append(subgroup)
                subgroup = []
                subgroup_len = 0

        return totalSubgroup, subgroup_len_list

    def belongToTheSame(self, selector1, selector2):
        # print('start')
        # print('selector1:',selector1.xpath('string(.)').extract_first())
        # print('selector2:',selector2.xpath('string(.)').extract_first())
        i = 0
        while True:
            siblings = selector1.xpath('./following-sibling::*')
            if selector2 in siblings:
                return i
            else:
                while i < 5:
                    i += 1
                    father_selector1 = selector1.xpath('./..')
                    father_selector2 = selector2.xpath('./..')
                    id_2 = id(father_selector2)
                    if father_selector1.extract() == father_selector2.extract():
                        return i
                    else:
                        # print(i)
                        # if self.judgeFromParent(selector1,selector2)
                        selector1 = father_selector1
                        # print('father_selector1:',selector1.xpath('string(.)').extract_first())
                        selector2 = father_selector2
                        # print('father_selector2:',selector2.xpath('string(.)').extract_first())
                return i

    def judgeFromAncestor(self, selector1, selector2):
        str1 = selector1.xpath('.').extract_first()
        str2 = selector2.xpath('.').extract_first()
        epsilon = 4
        for i in range(epsilon):
            str1_parent = selector1.xpath('./..')
            str2_parent = selector2.xpath('./..')
            diff_1 = str1_parent.extract_first().replace(str1, '')
            diff_2 = str2_parent.extract_first().replace(str2, '')
            length = (len(diff_1) + len(diff_2)) * 1.0 / 2
            distance = self.levenshteinDistance(diff_1, diff_2) * 1.0 / length
            if distance > 0.1:
                return False
            selector1 = str1_parent
            selector2 = str2_parent
        return True

    def getTitleAndText(self,response):
        #自动识别标题算法
        doc = Title(response.text, url=response.url)
        title = doc.short_title()

        #自动识别正文算法
        article = ArticleWithAttachment(response.text, url=response.url)
        myarticle = article.getArticleWithAttachment(response)
        return title,myarticle

    def judgeXpathFromText(self,txt):
        """
        判断txt是xpath还是普通的文本
        :param txt:
        :return True or False:
        """
        if '/html' in txt or '//*' in txt:
            return True
        return False


    def extractDate(self,txt):
        # re_data_1 = re.compile("(\d{4}-\d{1,2}-\d{1,2})")
        # re_data_2 = re.compile("(\d{4}年\d{1,2}月\d{1,2}日)")
        # re_data_3 = re.compile("(\d{4}\.\d{1,2}\.\d{1,2})")
        re_data = re.compile(r"(\d{4}-\d{1,2}-\d{1,2})|(\d{4}年\d{1,2}月\d{1,2})|(\d{4}\.\d{1,2}\.\d{1,2})")
        date = re.findall(re_data,txt)
        if date:
            for element in date[0]:
                if element:
                    if '年' in element:
                        element = element.replace('年','-').replace('月','-')
                    return element
        return None


