    # xpathList = []
    # combination = []
    #
    # item = MyItem()
    # tabel_name = 'policy'
    #
    # scrapyList = getScrapyList()
    # print('myfinal:%s' % getScrapyList())
    #
    # sql_order = "select COLUMN_NAME from information_schema.COLUMNS where table_name = '{}'".format(
    #     tabel_name)
    # cursor = self.conn.cursor()
    # cursor.execute(sql_order)
    # result = cursor.fetchall()
    #
    # # 把字段名和对应的xpath组合
    # if scrapyList:
    #     for r in result:
    #         xpathList.append(r[0])  # 字段
    #     for i in zip(scrapyList, xpathList):
    #         if i[0] and i[1]:
    #             combination.append(i)
    #
    #     for c in combination:
    #         item[c[1]] = response.xpath(c[0]).extract_first()
    # else:
    #     pass
import re
import pymysql
Hbody = "11231314"
date = re.search('\d{4}[^0-9]\d{2}[^0-9]\d{2}', Hbody)
if date:
    print(date.group())
else:
    print("AAA")
connect = pymysql.connect(
        host='127.0.0.1',
        user='root',
        passwd='root',
        db='scrapyTool',
        charset='utf8',
        port=3306)
sql_order = "CREATE TABLE IF NOT EXISTS 打测试(主题 VARCHAR(200) ,时间 text)"
cur = connect.cursor()
cur.execute(sql_order)
connect.close()

# 临时自定义方案
# @app.route('/new2', methods=['GET', 'POST'])
# def new2():
#     # 利用flask机制
#     tb = request.form.get("tb_name")
#     dis = request.form.get("dis_name")
#     add_tp = []
#     for i in range(16):
#         add_in = "add_" + str(i)
#         add_value = request.form.get(add_in)
#         if add_value != '' and add_value is not None:
#             add_tp.append(add_value)
#     # print(add_tp)
#
#     # 创建数据库表
#     tb_sql = "CREATE TABLE IF NOT EXISTS {}({} VARCHAR(15) PRIMARY KEY ,{} VARCHAR(15))".format(
#         tb, add_tp[0], add_tp[1])
#     connect = con()
#     with connect:
#         cur = connect.cursor()
#         cur.execute(tb_sql)
#         # cur.execute(insert_sql)
#         for temp in add_tp[2:]:
#             if temp:
#                 add_sql = "ALTER TABLE {} ADD {} VARCHAR(15)".format(tb, temp)
#                 cur.execute(add_sql)
#             else:
#                 break
#         t = query_col(cur, tb)
#     form = SubForm()
#     return render_template("temp.html", t=t, temp_form=form)