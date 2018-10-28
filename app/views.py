import os, random, json, logging
import time

from flask import render_template, request, redirect, url_for
from .forms import SubForm, DefaultForm
from scrapy import cmdline
from multiprocessing import Pool
import pymysql
import redis
from app import app
from .setting import *
import numpy as np
import collections
import json
from app.User import UserInfo

r = redis.Redis(host=RHOST, port=RPORT)
logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
                    filename='new.log',
                    filemode='a',  ##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
                    # a是追加模式，默认如果不写的话，就是追加模式
                    format=
                    '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    # 日志格式
                    )


# mysql数据库连接
def con():
    connect = pymysql.connect(
        host=HOST,
        user=USER,
        passwd=PASSWD,
        db=DB,
        charset=ENCODE,
        port=PORT,
        autocommit=True)
    return connect


# 取得要存储的表格的字段名
def query_col(cur, MyType):
    sql_order = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}'".format(MyType)
    cur.execute(sql_order)
    result = cur.fetchall()  # ((,) ,)
    temp = ()
    for my in result:
        temp = temp + my
    return temp


# 执行sql查询语句，取得结果
def query_tb(cur, sql_order):
    cur.execute(sql_order)
    result = cur.fetchall()
    return result


# todo 主要用于切换选项
@app.route('/', methods=['GET', 'POST'])
def root():
    fields_chinese_name_list = []
    # 中英文对照字典
    table_name_dict = {}
    table_name_chinese = ""
    table_name = request.values.get("Type")  # 获取爬取类型
    form = SubForm()  # 实例化表单类
    default_form = DefaultForm()
    user_id = str(random.randint(0, 100000))
    connect = con()
    cur = connect.cursor()
    sql_order = "SELECT table_name,table_name_in_db FROM {}".format(GENRAL_TABLE)
    # 中文表名-英文表名的配对tuple
    table_name_chinese_english_tuple = query_tb(cur, sql_order)

    for temp_tuple1 in table_name_chinese_english_tuple:
        table_name_dict[temp_tuple1[1]] = temp_tuple1[0]
    for temp_k in table_name_dict.keys():
        if table_name == temp_k:
            table_name_chinese = table_name_dict[temp_k]

    if table_name and table_name != 'custom':
        t = query_col(cur, table_name)
    else:
        t = ()
    for k in DISPLAY.keys():
        for kt in t:
            if k in kt:
                # print(DISPLAY[k])
                fields_chinese_name_list.append(DISPLAY[k])

    connect.close()
    return render_template(
        "index.html",
        form=form,
        default_form=default_form,
        tuple1=table_name_chinese_english_tuple,
        t=fields_chinese_name_list,
        name=table_name_chinese,
        append_id=user_id,
        table_name=table_name
    )


# todo 采集数据
@app.route('/scrapy', methods=['GET', 'POST'])
def scrapy():
    form = SubForm()
    default_form = DefaultForm()
    if not (form.validate_on_submit() or default_form.validate_on_submit()):
        return redirect(url_for('root'))

    result = 0
    default_crawl_flag = 0

    way = request.form.get("cus")
    table_name = request.form.get('table_name')
    select = request.form.get("option")
    page_num = request.form.get("page")
    selenium_page = request.form.get("selenium_num")
    url_list_xpath = request.form.get("list_xpath")
    append_idt = request.form.get("append")
    input_xpath = request.form.get("input_xpath")
    website = form.website.data

    # mode:1.Tool(quick three layer mode) 2. content(slow two layer mode) 3.selenium(slow three layer mode)
    model = "Tool"
    if select == "two":
        model = "content"

    if way == "nodefault":
        fields_xpath_list = []
        for i in range(33):
            tb = "tb" + str(i)
            fields_xpath_list.append(request.form.get(tb))
        for list in fields_xpath_list:
            result = result or list
        if not result:
            return "未填写class或id属性"
    else:
        default_website = request.form.get('website_url')
        website = default_website
        default_crawl_flag = 1

    user = UserInfo()

    user['user_id'] = append_idt
    user['website'] = website
    user['table_name'] = table_name
    user['default_crawl_flag'] = default_crawl_flag
    user['two_or_three_mode'] = model
    user['fields_xpath_list'] = fields_xpath_list
    # 只用于两层爬取的页码输入
    user['page_num'] = page_num
    #  是否存储数据
    user['if_store_data'] = 'start'
    user['error_msg'] = '正在爬取中'
    user['url_list_xpath'] = url_list_xpath
    user['page_num_xpath_list'] = input_xpath
    # 3层爬取中从默认的快速爬取模式切换到慢速爬取后的页码数码
    user['selenium_page'] = selenium_page
    # 存储爬取结果
    user['crawling_result'] = {}
    # 爬虫的默认状态
    user['spider_state'] = 'open'
    # r = redis.Redis(host=RHOST, port=RPORT)
    r.set(user['user_id'], user.to_json())
    print('user:', json.dumps(user))

    # 切换目录执行爬虫
    if "scrapyTool" not in os.getcwd():
        os.chdir("./scrapyTool")
    # logging.debug("pwd is :%s" % os.getcwd())
    po = Pool(10)  # 定义一个进程池，最大进程数10
    po.apply_async(scrapyprocess, (user['user_id'], user['two_or_three_mode'],))
    return render_template("middle.html", append_idt=append_idt)


# todo 多进程
def scrapyprocess(append_idt, model="Tool"):
    cmdline.execute(("scrapy crawl %s -a id=%s" % (model, append_idt)).split())


# todo 同于新增栏目/待解决插入数据重复
# @app.route('/new1', methods=['GET', 'POST'])
# def new1():
#     tb = request.form.get("tb_name")  # 用于数据库中的存储
#     dis = request.form.get("dis_name")  # 用于网页端的显示
#     add = []
#     for i in range(33):
#         add_in = "add_" + str(i)
#         add_value = request.form.get(add_in)
#         if add_value is not '' or None:
#             add.append(add_value)
#     tb_sql = "CREATE TABLE IF NOT EXISTS {}({} VARCHAR(200)) CHARSET=utf8".format(tb, add[0])
#     insert_sql = "insert ignore into table_summary values(null,'{}','{}');".format(dis, tb)
#     connect = con()
#     with connect:
#         cur = connect.cursor()
#         cur.execute(tb_sql)
#         cur.execute(insert_sql)
#         for temp in add[1:]:
#             if temp:
#                 add_sql = "ALTER TABLE {} ADD {} text".format(tb, temp)
#                 cur.execute(add_sql)
#             else:
#                 break
#         web_sql = "ALTER TABLE {} ADD {} text".format(tb, "网址")
#         cur.execute(web_sql)
#     return redirect(url_for('root'))


# 临时采集界面
# @app.route('/new2', methods=['GET', 'POST'])
# def new2():
#     r = redis.Redis(host=RHOST, port=RPORT)
#
#
#     global website
#     global cur_type
#     website = request.form.get('url_name')
#     tb = request.form.get("tb_name")
#     cur_type = tb
#     append_idt = request.form.get("append")
#     add_tp = []
#     for i in range(33):
#         add_insert = "seg" + str(i)
#         add_value = request.form.get(add_insert)
#         if add_value != '' and add_value is not None:
#             add_tp.append(add_value)
#     # 创建数据库的表
#     tb_sql = "CREATE TABLE IF NOT EXISTS {}({} VARCHAR(200)) CHARSET=utf8".format(tb, add_tp[0])
#
#     connect = con()
#     with connect:
#         cur = connect.cursor()
#         cur.execute(tb_sql)
#         for temp in add_tp[1:]:
#             if temp:
#                 add_sql = "ALTER TABLE {} ADD {} text)".format(tb, temp)
#                 cur.execute(add_sql)
#             else:
#                 break
#         web_sql = "ALTER TABLE {} ADD {} text".format(tb, "网址")
#         cur.execute(web_sql)
#     scrapy_list.clear()
#     for i in range(33):
#         tb = "xpath_" + str(i)
#         scrapy_list.append(request.form.get(tb))
#     if "scrapyTool" not in os.getcwd():
#         os.chdir("./scrapyTool")
#     po = Pool(10)  # 定义一个进程池，最大进程数3
#     po.apply_async(scrapyprocess, (append_idt,))
#     return render_template("middle.html", append_idt=append_idt)


@app.route('/result', methods=['GET', 'POST'])
def get_result():
    """
    F:从redis里获取并显示采集结果
    """


    new_dis = []
    id = request.form.get("append")
    # r = redis.Redis(host=RHOST, port=RPORT)
    th, dis, error_msg = group(r, id)
    # print('mydis:', dis)
    # print('myth:', th)

    th_alis = []
    if th:
        for th_ in th:
            if 'url' in th_:
                th_alis.append('网址')
            elif 'text' in th_:
                th_alis.append('正文')
            elif 'title' in th_:
                th_alis.append('标题')

            for k in DISPLAY.keys():
                if k in th_:
                    th_alis.append(DISPLAY[k])

    if not dis:
        return render_template("result.html", id=id,error_msg=error_msg)

    for temp in dis[0]:
        new_dis.append([])
    for i in range(len(dis[0])):
        for cont in dis:
            new_dis[i].append(cont[i])
    # print("new_dis:", new_dis)
    return render_template("result.html", th=th_alis, dis=new_dis[:30], id=id, error_msg=error_msg)


@app.route('/results?id=<id>', methods=['GET', 'POST'])
def get_results(id):


    new_dis = []
    # r = redis.Redis(host=RHOST, port=RPORT)
    th, dis, error_msg = group(r, id)
    # print('myth:', th)
    # print('mydis:', dis)

    th_alis = []
    if th:
        for th_ in th:
            if 'url' in th_:
                th_alis.append('网址')
            elif 'text' in th_:
                th_alis.append('正文')
            elif 'title' in th_:
                th_alis.append('标题')

            for k in DISPLAY.keys():
                if k in th_:
                    th_alis.append(DISPLAY[k])

    if not dis:
        return render_template("result.html", id=id)
    for _ in dis[0]:
        new_dis.append([])
    for i in range(len(dis[0])):
        for cont in dis:
            new_dis[i].append(cont[i])

    print('th_ais:', th_alis)
    print('new_dis:', new_dis[:30])

    return render_template("result.html", th=th_alis, dis=new_dis[:30], id=id, error_msg=error_msg)


# 用于向pipeline传递数据(切换到selenium慢速模式)
def storeData(userinfo):
    table_name = userinfo['table_name']
    crawling_result = userinfo['crawling_result']
    keys = crawling_result.keys()
    values = tuple(crawling_result.values())
    length = len(values)
    params = ['%s'] * length
    sql_data = []
    sql = 'insert into %s(%s) values(%s)' % (table_name, ','.join(list(keys)), ','.join(params))
    cur = con().cursor()
    try:
        for i in zip(*values):
            cur.execute(sql, i)
    except Exception as e:
        print('there is sth wrong with data storing after spider closed')
        logging.debug(e)
        logging.info(e)
    finally:
        pass


@app.route('/crawling', methods=['GET', 'POST'])
def crawling():
    # r = redis.Redis(host=RHOST, port=RPORT)
    # 是否存储
    is_save = request.form.get('save')
    # 用户id(随机数)
    id = request.form.get('append')
    userinfo = UserInfo.from_json(r.get(id))

    if is_save:
        userinfo['if_store_data'] = is_save
        r.set(id, userinfo.to_json())
    if not is_save:
        is_save = userinfo['if_store_data']
    logging.info('用户选择是否存储爬取结果:%s'%is_save)
    if is_save:
        if "sw" in str(is_save):
            logging.info(is_save)

            userinfo['crawling_result'] = {}
            userinfo['spider_state'] = 'open'
            userinfo['if_store_data'] = 'start'

            # userinfo['crawling_result'] = {}
            # if userinfo['spider_state'] == 'close':
            #     userinfo['if_store_data'] = 'start'
            # else:userinfo['if_store_data'] = 'nosw'
            #等待spider关闭并调用close()方法
            # time.sleep(10)
            # userinfo['spider_state'] = 'open'

            userinfo['error_msg'] = '正在爬取中'
            r.set(id, userinfo.to_json())
            time.sleep(2)
            logging.info('userinfo in crawling:%s'% UserInfo.from_json(r.get(id))['crawling_result'])
            po = Pool(10)
            logging.info('before')
            logging.info('after:%s'%UserInfo.from_json(r.get(id))['spider_state'])
            time.sleep(5)
            po.apply_async(scrapyprocess, (id, "selenium",))

        if 'no' == str(is_save):
            userinfo['crawling_result'] = {}
            userinfo['spider_state'] = 'close'
            userinfo['if_store_data'] = 'no'
            userinfo['error_msg'] = '爬虫已经关闭'
            r.set(id, userinfo.to_json())

    # 用于保存当爬虫结束但是没有及时点击保存按钮的情况
    userinfo = UserInfo.from_json(r.get(id))
    print('userinfo_in_crawling:', userinfo)
    if userinfo['spider_state'] == 'nature_close' and 'yes' in str(is_save):
        logging.debug('views关闭了')
        storeData(userinfo)
        logging.info('数据保存后删除缓存')
        logging.info('居然关闭了')
        r.delete(id)
    if userinfo['spider_state'] == 'nature_close' and str(is_save) == 'no':
        logging.info('用户选择"停止并丢弃"按钮后删除缓存')
        logging.info('居然关闭了2')
        r.delete(id)
    return redirect(url_for('get_results', id=id))


def group(r, id):
    """
    合成redis数据为[[,],]
    :return:
    """
    # id = str(random.randint(0, 10000))
    # print(id, type(id))
    if r.get(id):
        userinfo = UserInfo.from_json(r.get(id))
    else:
        # return None,None,None
        return None,None,'正在'
    error_msg = userinfo['error_msg']
    # print('userinfo_in_group:', userinfo['crawling_result'])
    # print('userinfo_in_group:',userinfo['if_store_data'])
    key = []  # 按字段名索引
    th = None
    get_th = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}'".format(userinfo['table_name'])
    connect = con()
    with connect:
        cur = connect.cursor()
        cur.execute(get_th)
        th = cur.fetchall()
    for seg in th:
        key.append(seg[0])
    totalNo = 0
    keyExists = np.zeros((len(key), 1))
    for i in np.arange(len(key)):
        t = userinfo['crawling_result'].get(key[i], None)
        if t:
            keyExists[i] = 1
            totalNo += 1
    if totalNo == 0:
        return None, None,error_msg
    else:
        index = np.nonzero(keyExists)[0]
        key_defined = np.array(key)[index]
        # print('key_defined:',key_defined)
        # dis = [list(map(lambda x: x.decode('utf-8'), userinfo['crawling_result'].get(k))) for k in key_defined]
        # dis = [userinfo['crawling_result'].get(k) for k in key_defined]
        dis = [list(map(lambda x:str(x),userinfo['crawling_result'].get(k))) for k in key_defined]
        return key_defined.tolist(), dis, error_msg
