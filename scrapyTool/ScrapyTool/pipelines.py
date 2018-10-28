# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import time

import redis,logging
import pymysql
from app.setting import *
from app.User import UserInfo
# from app.views import getCurType
import requests
from scrapy.exceptions import CloseSpider

logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                     filename='new.log',
                     filemode='a',  ##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                     # a是追加模式，默认如果不写的话，就是追加模式
                     format=
                     '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                     # 日志格式
                     )


class ScrapytoolPipeline(object):
    def __init__(self):
        self.db = pymysql.connect(host=HOST, user=USER, passwd=PASSWD, db=DB, charset='utf8', port=PORT,
                                  autocommit=True)
        self.cursor = self.db.cursor()
        self.r = redis.StrictRedis(host=RHOST, port=RPORT)
        self.preitem = []
        self.flag = None

    def open_spider(self, spider):
        spider.myPipeline = self

    def process_item(self, item, spider):
        logging.info('helloworld1')
        self.id = getattr(spider, "aid")
        logging.info('helloworld2')
        logging.info('the id in pipeline:{}'.format(self.id))
        logging.info('the userinfo in pipeline is :%s'%len(self.r.get(self.id)))
        self.userinfo = UserInfo.from_json(self.r.get(self.id))
        self.table_name = self.userinfo['table_name']
        self.mid = self.userinfo['if_store_data']
        self.flag = str(self.mid)
        logging.info('the flag in pipelines:%s'%self.flag)
        if 'yes' not in self.flag:
            logging.debug('用户还没有点击保存按钮')
            self.preitem.append(item)
        if 'yes' in self.flag:
            if self.preitem is not None:
                logging.debug('first restore data from redis to database')
                self.storeData()
                self.preitem = None
            logging.debug('piplines:start to process items')
            params = []
            values = []
            for k, v in item.fields.items():
                params.append('%s')
                value = item._values[k]
                values.append(value)

            sql = 'insert into %s(%s) values(%s)' % (self.table_name, ','.join(item.fields.keys()), ','.join(params))

            try:
                # print('pipeline_tuple:%s'%tuple(values))
                # self.cursor.execute(sql,(','.join(values)))
                print(values)
                self.cursor.execute(sql, tuple(values))
            except Exception as error:
                print('sql error .................................')
                print('error:', error)
            return item

    def getFlag(self):
        return self.flag

    def storeData(self):
        for item in self.preitem:
            data = dict(item)
            keys = ','.join(data.keys())
            values = ','.join(['%s'] * len(data))
            sql = 'insert into %s (%s) values (%s)' % (self.table_name, keys, values)
            print('sql str:',sql)
            self.cursor.execute(sql, tuple(data.values()))
            self.db.commit()

    def close_spider(self, spider):
        pass
        # print('preitem:', self.preitem)
        # print(len(self.preitem))
        # if self.flag == "yes":
        #     self.storeData()
        # self.db.close()


class RedisPipeline(object):
    def __init__(self):
        self.r = redis.StrictRedis(host=RHOST, port=RPORT)
        # self.key = []

    def process_item(self, item, spider):
        self.id = getattr(spider, "aid")
        self.userinfo = UserInfo.from_json(self.r.get(self.id))
        print('userinfo in redis pipeline:',self.userinfo)
        logging.debug('piplines:start to Redis items')
        data = dict(item)
        # if not self.key:
        #     for k in data.keys():
        #         k = k + self.id
        #         self.key.append(k)

        for k, v in data.items():
            data_stored = self.userinfo['crawling_result']
            data_ = data_stored.get(k,[])
            data_.append(v)
            data_stored[k] = data_
        self.r.set(self.id, self.userinfo.to_json())
        return item

    def close_spider(self, spider):
        # self.userinfo['crawling_result'] = {}
        # self.r.set(self.id,self.userinfo.to_json())
        print('close_spider in redis pipeline:',self.userinfo['crawling_result'])
        pass
        # for k in self.key:
        #     self.r.delete(k)
        # self.r.delete(self.id)

#for twospider
class TestPipeline(object):
    def __init__(self):
        self.r = redis.StrictRedis(host=RHOST, port=RPORT)
        # self.curType = getCurType()
        # print('pipeline_curtype:%s' % self.curType)

        self.db = pymysql.connect(host=HOST, user=USER, passwd=PASSWD, db=DB, charset='utf8', port=PORT,
                                  autocommit=True)
        self.cursor = self.db.cursor()

        self.preitem = []
        self.flag = None

    def open_spider(self, spider):
        spider.myPipeline = self

    def process_item(self, item, spider):
        self.id = getattr(spider, "aid")
        self.userinfo = UserInfo.from_json(self.r.get(self.id))
        self.table_name = self.userinfo['table_name']
        # resp = requests.get("http://localhost:9998/crawling?append=%s" % self.id)
        # self.flag = resp.text
        # print('the flag:', self.flag)
        # print('type:',type(self.flag))
        # if self.flag:
        #     self.flag = str(self.flag,encoding='utf-8')
        self.mid = self.userinfo['if_store_data']
        self.flag = str(self.mid)
        print("My pipe flag is:", self.flag)

        if 'yes' not in self.flag:
            print('用户还没有输入')
            self.preitem.append(item)

        if 'yes' in self.flag:
            if self.preitem is not None:
                self.storeData()
                self.preitem = None

            final_list = []
            data = dict(item)
            v_list_length = len(list(data.values())[0])
            for i in range(v_list_length):
                final_list.append({})
            keys = ','.join(data.keys())
            values = ','.join(['%s'] * len(data))

            for i in range(v_list_length):
                for key in data.keys():
                    final_list[i][key] = data[key][i]
            print("final_list22222", final_list)
            sql = 'insert into %s(%s) values(%s)' % (self.table_name, keys, values)
            # params = []
            # values = []
            # for k, v in item.fields.items():
            #     params.append('%s')
            #     value = item._values[k]
            #     values.append(value)
            # sql = 'insert into %s(%s) values(%s)' % (self.curType, ','.join(item.fields.keys()), ','.join(params))

            try:
                for sub_dict in final_list:
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
            sql = 'insert into %s(%s) values(%s)' % (self.table_name, keys, values)
            for sub_dict in final_list:
                print("sub_dict", sub_dict.values())
                self.cursor.execute(sql, tuple(sub_dict.values()))

    def close_spider(self, spider):
        pass
        # print('close_spider_preitem:', self.preitem)
        # if self.flag == "yes":
        #     self.storeData()
        # self.db.close()
