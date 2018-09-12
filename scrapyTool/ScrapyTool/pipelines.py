# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time

import redis
import pymysql
from app.setting import *
from app.views import getCurType
import requests
from scrapy.exceptions import CloseSpider


class ScrapytoolPipeline(object):
    def __init__(self):
        self.curType = getCurType()
        print('pipeline_curtype:%s' % self.curType)

        self.db = pymysql.connect(host=HOST, user=USER, passwd=PASSWD, db=DB, charset='utf8', port=PORT,
                                  autocommit=True)
        self.cursor = self.db.cursor()
        self.r = redis.StrictRedis(host='localhost', port=6379)
        self.preitem = []
        self.flag = None

    def open_spider(self, spider):
        spider.myPipeline = self

    def process_item(self, item, spider):
        self.id = getattr(spider, "aid")
        self.mid = self.r.get(self.id)
        self.flag = str(self.mid)
        # resp = requests.get("http://localhost:9998/crawling?append=%s" % self.id)
        # self.flag = resp.text
        # print('the flag:', self.flag)
        print('type:', type(self.flag))
        # if self.flag:
        #     self.flag = str(self.flag,encoding='utf-8')
        print("My pipe flag is:", self.flag)

        if 'yes' not in self.flag:
            print('用户还没有输入')
            self.preitem.append(item)
        # print("Preitem", self.preitem)

        if 'yes' in self.flag:
            if self.preitem is not None:
                print('first to restore the data in redis')
                self.storeData()
                self.preitem = None
            print('piplines:start to process items')
            params = []
            values = []
            for k, v in item.fields.items():
                params.append('%s')
                value = item._values[k]
                values.append(value)

            sql = 'insert into %s(%s) values(%s)' % (self.curType, ','.join(item.fields.keys()), ','.join(params))

            try:
                # print('pipeline_tuple:%s'%tuple(values))
                # self.cursor.execute(sql,(','.join(values)))
                print(values)
                self.cursor.execute(sql, tuple(values))
            except Exception as error:
                print('sql error .................................')
                print('error:', error)
            return item
        # elif 'no' in self.flag:
        #     print("it is no save")
        #     # raise CloseSpider('terminated lol')
        #     # p = multiprocessing.current_process()
        #     # print('process:',p.name)
        #     # p.terminate()
        #     # print('just stopped')
        #     # p.join()
        #
        #     spider.crawler.engine.close_spider(spider)
        #     print('oh yehr')
        #     # self.close_spider(spider)
        # else:
        #     print('user has not choose yet')

    def getFlag(self):
        return self.flag

    def storeData(self):
        for item in self.preitem:
            data = dict(item)
            keys = ','.join(data.keys())
            values = ','.join(['%s'] * len(data))
            sql = 'insert into %s (%s) values (%s)' % (self.curType, keys, values)
            self.cursor.execute(sql, tuple(data.values()))
            self.db.commit()

    def close_spider(self, spider):
        print('preitem:', self.preitem)
        print(len(self.preitem))
        if self.flag == "yes":
            self.storeData()
        self.db.close()


class RedisPipeline(object):
    def __init__(self):
        self.r = redis.StrictRedis(host='localhost', port=6379)
        self.key = []

    def process_item(self, item, spider):
        self.id = getattr(spider, "aid")
        print('piplines:start to Redis items', type(item))
        print("redis:", item)
        data = dict(item)
        if not self.key:
            for k in data.keys():
                k = k + self.id
                self.key.append(k)

        for k, v in data.items():
            k = k + self.id
            print(k, v)
            self.r.lpush(k, v)
        return item

    def close_spider(self, spider):
        # pass
        for k in self.key:
            self.r.delete(k)
        self.r.delete(self.id)


class TestPipeline(object):
    def __init__(self):
        self.curType = getCurType()
        print('pipeline_curtype:%s' % self.curType)

        self.db = pymysql.connect(host=HOST, user=USER, passwd=PASSWD, db=DB, charset='utf8', port=PORT,
                                  autocommit=True)
        self.cursor = self.db.cursor()

        self.preitem = []
        self.flag = None

    def open_spider(self, spider):
        spider.myPipeline = self

    def process_item(self, item, spider):
        self.id = getattr(spider, "aid")
        # resp = requests.get("http://localhost:9998/crawling?append=%s" % self.id)
        # self.flag = resp.text
        # print('the flag:', self.flag)
        # print('type:',type(self.flag))
        # if self.flag:
        #     self.flag = str(self.flag,encoding='utf-8')
        self.mid = self.r.get(self.id)
        self.flag = str(self.mid)
        print("My pipe flag is:", self.flag)

        if 'yes' not in self.flag:
            print('用户还没有输入')
            self.preitem.append(item)

        print("Preitem", self.preitem)

        if 'yes' in self.flag:
            if self.preitem is not None:
                print('first to restore the data in redis')
                self.storeData()
                self.preitem = None
            print('piplines:start to process items')

            final_list = []
            data = dict(item)
            v_list_length = len(list(data.values())[0])
            for i in range(v_list_length):
                final_list.append({})
            print("final_list11111", final_list)
            keys = ','.join(data.keys())
            values = ','.join(['%s'] * len(data))

            for i in range(v_list_length):
                for key in data.keys():
                    final_list[i][key] = data[key][i]
            print("final_list22222", final_list)
            sql = 'insert into %s(%s) values(%s)' % (self.curType, keys, values)
            # params = []
            # values = []
            # for k, v in item.fields.items():
            #     params.append('%s')
            #     value = item._values[k]
            #     values.append(value)
            # sql = 'insert into %s(%s) values(%s)' % (self.curType, ','.join(item.fields.keys()), ','.join(params))

            try:
                # print('pipeline_tuple:%s'%tuple(values))
                # self.cursor.execute(sql,(','.join(values)))
                for sub_dict in final_list:
                    print("sub_dict", sub_dict.values())
                    self.cursor.execute(sql, tuple(sub_dict.values()))
            except Exception as error:
                print('sql error .................................')
                print('error:', error)
            return item
        # elif 'no' in self.flag:
        #     print("it is no save")
        #     # raise CloseSpider('terminated lol')
        #     # p = multiprocessing.current_process()
        #     # print('process:',p.name)
        #     # p.terminate()
        #     # print('just stopped')
        #     # p.join()
        #
        #     spider.crawler.engine.close_spider(spider)
        #     print('oh yehr')
        #     # self.close_spider(spider)
        # else:
        #     print('user has not choose yet')

    def getFlag(self):
        return self.flag

    def storeData(self):
        for item in self.preitem:
            final_list = []
            data = dict(item)
            list_contain = list(data.values())
            v_list_length = len(list(data.values())[0])
            for i in range(v_list_length):
                final_list.append({})
            print("final_list", final_list)
            keys = ','.join(data.keys())
            values = ','.join(['%s'] * len(data))

            for i in range(v_list_length):
                for key in data.keys():
                    final_list[i][key] = data[key][i]
            print("final_list", final_list)
            sql = 'insert into %s(%s) values(%s)' % (self.curType, keys, values)
            for sub_dict in final_list:
                print("sub_dict", sub_dict.values())
                self.cursor.execute(sql, tuple(sub_dict.values()))
            # self.db.commit()

    def close_spider(self, spider):
        print('close_spider_preitem:', self.preitem)
        if self.preitem:
            print(len(self.preitem))
        if self.flag == "yes":
            self.storeData()
        self.db.close()
