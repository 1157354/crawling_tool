from scrapy.exceptions import CloseSpider
import re
import scrapy
import pymysql

from app.setting import *
from scrapy_splash import SplashRequest

from app.views import getScrapyList
from app.views import getWebsite
from app.views import getCurType
from app.views import getDefaultFlag
from app.views import getlistxpath

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


class ToolSpider(scrapy.Spider):
    name = "Tool"

    def __init__(self, id='', **kwargs):
        super(ToolSpider, self).__init__(**kwargs)
        self.conn = pymysql.connect(host=HOST, user=USER, passwd=PASSWD, db=DB, charset='utf8', port=PORT)
        self.cursor = self.conn.cursor()
        self.aid = id
        print("aid:", self.aid)
        self.bloom = BloomFilter(max_elements=100000, error_rate=0.05)
        self._getWebsitesInDB()

    def _getWebsitesInDB(self):
        table_name = getCurType()
        print("getCurType", table_name)
        sql = 'select 网址 from %s' % table_name
        self.cursor.execute(sql)
        results = self.cursor.fetchall()
        print("results", results, len(results))
        if results is not None:
            for r in results:
                self.bloom.add(r[0])

    def start_requests(self):
        website = getWebsite()
        yield SplashRequest(url=website, callback=self.parse, endpoint='execute',
                            args={'lua_source': first_script, 'wait': 3, 'NEXTPAGE_KEYWORD': 'next', 'page': 1})

    def parse(self, response):
        list_a = getlistxpath()
        # 接收到xpath则用xpath解析列表
        # //div[@class="m2"]/ul//h3
        if list_a:
            list_href = list_a + '//a/@href'
            list_urls = response.xpath(list_href).extract()
            list_urls = list(set(list_urls))
            final_urls = list_urls[:]
            for url in list_urls:
                if url == '#' or "javascript" in url:
                    final_urls.remove(url)
            print("final_urls", len(final_urls))
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
        default_flag = getDefaultFlag()
        xpathList = []
        combination = []
        item = MyItem()
        table_name = getCurType()
        print("table_name is ", table_name)

        finalFlag = self.myPipeline.getFlag()
        print("finalFlag", finalFlag)
        if finalFlag:
            if 'no' in finalFlag:
                raise CloseSpider('用户不想继续爬取')

        # 标题
        doc = Title(response.text, url=response.url)
        title = doc.short_title()
        print('ttitle:', title)

        # 正文
        article = ArticleWithAttachment(response.text, url=response.url)
        myarticle = article.getArticleWithAttachment(response)

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
        # try:
        #     print(date.group())
        #     item['发文日期'] = date.group()
        # except BaseException:
        #     print('无日期')
        #     item['发文日期'] = ""

        if default_flag == 1:
            print('---default crawl---')
            item['标题'] = title
            print('tttiitle:', title)
            item['正文'] = myarticle
            if date:
                item['发文日期'] = date.group()
            else:
                item['发文日期'] = ""
            item['网址'] = response.url
            print("the item is :", item)
            yield item


        # 非默认爬取功能
        else:
            print('---crawl start---')
            scrapyList = getScrapyList()
            sql_order = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}'".format(table_name)
            cursor = self.conn.cursor()
            cursor.execute(sql_order)
            result = cursor.fetchall()

            for r in result:
                xpathList.append(r[0])
            for i in zip(scrapyList, xpathList):
                if i[0] and i[1]:
                    combination.append(i)

            for c in combination:
                item[c[1]] = response.xpath(c[0]).extract_first()
                if c[1] == '标题':
                    item[c[1]] = title
                if c[1] == '正文':
                    item[c[1]] = myarticle
                if re.match(reDate, c[1]) != None:
                    item[c[1]] = date.group()
            item['网址'] = response.url
            yield item

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
