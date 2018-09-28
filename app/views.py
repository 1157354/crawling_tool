import os, random
from flask import render_template, request, redirect, url_for
from .forms import SubForm, DefaultForm
from scrapy import cmdline
from multiprocessing import Pool
import pymysql
import redis
from app import app
from .setting import *
import numpy as np
import logging

# logging.basicConfig(level=logging.DEBUG,  # 控制台打印的日志级别
#                     filename='new.log',
#                     filemode='a',  ##模式，有w和a，w就是写模式，每次都会重新写日志，覆盖之前的日志
#                     # a是追加模式，默认如果不写的话，就是追加模式
#                     format=
#                     '%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
#                     # 日志格式
#                     )

# 要被外部引用的变量
scrapy_list = []
default_list = []
add_tp = []
MyType = "通用政策模型"
cur_type = "通用政策模型"
tb = ""
dis = ""
website = ""
default_flag = ""
default_website = ""
is_save = ""
list_xpath = ""
page_num = ""
selenium_page = ""
input_xpath = ""


# mysql数据库连接
def con():
    connect = pymysql.connect(
        host=HOST,
        user=USER,
        passwd=PASSWD,
        db=DB,
        charset=ENCODE,
        port=PORT)
    return connect


def query_col(cur, MyType):
    sql_order = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}'".format(MyType)
    cur.execute(sql_order)
    result = cur.fetchall()  # ((,) ,)
    temp = ()
    for my in result:
        temp = temp + my
    return temp


def query_tb(cur, sql_order):
    cur.execute(sql_order)
    result = cur.fetchall()
    return result


# todo 主要用于切换选项
@app.route('/', methods=['GET', 'POST'])
def root():
    global cur_type
    # cur_type = request.values.get("Type")  # 获取爬取类型
    cur_dict = request.get_json()  # 获取爬取类型
    print(cur_dict)
    if cur_dict:
        cur_type = cur_dict.get("type_id")
    form = SubForm()  # 实例化表单类
    default_form = DefaultForm()
    append_id = str(random.randint(0, 10000))
    connect = con()
    cur = connect.cursor()
    sql_order = "SELECT table_name,table_name_in_db FROM table_summary"
    tuple1 = query_tb(cur, sql_order)
    if cur_type and cur_type != 'custom':
        t = query_col(cur, cur_type)
    else:
        t = query_col(cur, MyType)
        cur_type = "通用政策模型"
    print(t)
    print("cur_type_back", cur_type)
    connect.close()
    return render_template(
        "index.html",
        form=form,
        default_form=default_form,
        tuple1=tuple1,
        t=t,
        name=cur_type,
        append_id=append_id)


# todo 采集数据
@app.route('/scrapy', methods=['GET', 'POST'])
def scrapy():
    form = SubForm()
    default_form = DefaultForm()
    if not (form.validate_on_submit() or default_form.validate_on_submit()):
        return redirect(url_for('root'))

    result = 0
    global default_flag
    global default_website
    global website
    global list_xpath
    global page_num
    global selenium_page
    global input_xpath

    way = request.form.get("cus")
    select = request.form.get("option")
    page_num = request.form.get("page")
    selenium_page = request.form.get("selenium_num")
    list_xpath = request.form.get("list_xpath")
    append_idt = request.form.get("append")
    input_xpath = request.form.get("input_xpath")
    website = form.website.data

    model = "Tool"
    if select == "two":
        model = "content"

    if way == "nodefault":
        scrapy_list.clear()
        for i in range(33):
            tb = "tb" + str(i)
            scrapy_list.append(request.form.get(tb))
        for list in scrapy_list:
            result = result or list
        if not result:
            return "未填写class或id属性"
    else:
        default_website = request.form.get('website_url')
        website = default_website
        default_flag = 1

    # 切换目录执行爬虫
    if "scrapyTool" not in os.getcwd():
        os.chdir("./scrapyTool")
    # logging.debug("pwd is :%s" % os.getcwd())
    po = Pool(10)  # 定义一个进程池，最大进程数3
    po.apply_async(scrapyprocess, (append_idt, model,))
    return render_template("middle.html", append_idt=append_idt)


# todo 多进程
def scrapyprocess(append_idt, model="Tool"):
    cmdline.execute(("scrapy crawl %s -a id=%s" % (model, append_idt)).split())


# todo 同于新增栏目/待解决插入数据重复
@app.route('/new1', methods=['GET', 'POST'])
def new1():
    tb = request.form.get("tb_name")  # 用于数据库中的存储
    dis = request.form.get("dis_name")  # 用于网页端的显示
    add = []
    for i in range(33):
        add_in = "add_" + str(i)
        add_value = request.form.get(add_in)
        if add_value is not '' or None:
            add.append(add_value)
    tb_sql = "CREATE TABLE IF NOT EXISTS {}({} VARCHAR(200)) CHARSET=utf8".format(tb, add[0])
    insert_sql = "insert ignore into table_summary values(null,'{}','{}');".format(dis, tb)
    connect = con()
    with connect:
        cur = connect.cursor()
        cur.execute(tb_sql)
        cur.execute(insert_sql)
        for temp in add[1:]:
            if temp:
                add_sql = "ALTER TABLE {} ADD {} text".format(tb, temp)
                cur.execute(add_sql)
            else:
                break
        web_sql = "ALTER TABLE {} ADD {} text".format(tb, "网址")
        cur.execute(web_sql)
    return redirect(url_for('root'))


# 临时采集界面
@app.route('/new2', methods=['GET', 'POST'])
def new2():
    global website
    global cur_type
    website = request.form.get('url_name')
    tb = request.form.get("tb_name")
    cur_type = tb
    append_idt = request.form.get("append")
    add_tp = []
    for i in range(33):
        add_insert = "seg" + str(i)
        add_value = request.form.get(add_insert)
        if add_value != '' and add_value is not None:
            add_tp.append(add_value)
    # 创建数据库的表
    tb_sql = "CREATE TABLE IF NOT EXISTS {}({} VARCHAR(200)) CHARSET=utf8".format(tb, add_tp[0])

    connect = con()
    with connect:
        cur = connect.cursor()
        cur.execute(tb_sql)
        for temp in add_tp[1:]:
            if temp:
                add_sql = "ALTER TABLE {} ADD {} text)".format(tb, temp)
                cur.execute(add_sql)
            else:
                break
        web_sql = "ALTER TABLE {} ADD {} text".format(tb, "网址")
        cur.execute(web_sql)
    scrapy_list.clear()
    for i in range(33):
        tb = "xpath_" + str(i)
        scrapy_list.append(request.form.get(tb))
    if "scrapyTool" not in os.getcwd():
        os.chdir("./scrapyTool")
    po = Pool(10)  # 定义一个进程池，最大进程数3
    po.apply_async(scrapyprocess, (append_idt,))
    return render_template("middle.html", append_idt=append_idt)


# 用于向pipeline传递数据
@app.route('/crawling', methods=['GET', 'POST'])
def crawling():
    is_save = request.form.get('save')
    print('is_save:', is_save)
    id = request.form.get('append')
    print('my id:', id)
    r = redis.Redis(host=RHOST, port=RPORT)
    if is_save:
        r.set(id, is_save)
    if not is_save:
        is_save = r.get(id)
    print('is_save again:', is_save)
    if is_save:
        if "sw" in str(is_save):
            print("---开始切换---")
            po = Pool(10)
            po.apply_async(scrapyprocess, (id, "selenium",))
    return redirect(url_for('get_results', id=id))


@app.route('/result', methods=['GET', 'POST'])
def get_result():
    """
    F:从redis里获取并显示采集结果
    """
    new_dis = []
    id = request.form.get("append")
    r = redis.Redis(host=RHOST, port=RPORT)
    th, dis = group(r, id)
    if not dis:
        return render_template("result.html", id=id)

    for temp in dis[0]:
        new_dis.append([])
    for i in range(len(dis[0])):
        for cont in dis:
            new_dis[i].append(cont[i])
    print("new_dis:", new_dis)
    return render_template("result.html", th=th, dis=new_dis[:30], id=id)


@app.route('/results?id=<id>', methods=['GET', 'POST'])
def get_results(id):
    new_dis = []
    r = redis.Redis(host=RHOST, port=RPORT)
    th, dis = group(r, id)
    if not dis:
        return render_template("result.html", id=id)
    for temp in dis[0]:
        new_dis.append([])
    for i in range(len(dis[0])):
        for cont in dis:
            new_dis[i].append(cont[i])
    return render_template("result.html", th=th, dis=new_dis[:30], id=id)


def group(r, id):
    """
    合成redis数据为[[,],]
    :return:
    """
    print("group id", id)
    # id = str(random.randint(0, 10000))
    # print(id, type(id))
    key = []  # 按字段名索引
    th = None
    get_th = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}'".format(cur_type)
    connect = con()
    with connect:
        cur = connect.cursor()
        cur.execute(get_th)
        th = cur.fetchall()
    for seg in th:
        key.append(seg[0] + id)
    totalNo = 0
    keyExists = np.zeros((len(key), 1))
    for i in np.arange(len(key)):
        t = r.lrange('%s' % key[i], start=0, end=-1)
        if t:
            keyExists[i] = 1
            totalNo += 1
    if totalNo == 0:
        return None, None
    else:
        index = np.nonzero(keyExists)[0]
        key_defined = np.array(key)[index]
        dis = [list(map(lambda x: x.decode('utf-8'), r.lrange('%s' % k, start=0, end=-1))) for k in key_defined]
        return key_defined.tolist(), dis


def getScrapyList():
    return scrapy_list


def getWebsite():
    return website


def getCurType():
    return cur_type


def getDefaultFlag():
    return default_flag


def getDefaultList():
    return default_list


def getlistxpath():
    return list_xpath


def getpagenum():
    return page_num


def getpage():
    return selenium_page


def get_input_xpath():
    return input_xpath
