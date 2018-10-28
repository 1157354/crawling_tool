__author__ = 'tian'

DOWNLOAD_LOCATION = '/home/myuser/file/'

HOST = '115.233.227.46'
USER = 'root'
PASSWD = 'gov20130528'
DB = 'dips_cloud_gov'
ENCODE = 'utf8'
PORT = 7074

RHOST = '127.0.0.1'
RPORT = 6379
REDIS_PASSWORD = 'foobared'


#在数据库中的总表名字
GENRAL_TABLE = 'scrapy_table_summary'
#在前台页面上需要显示的字段及其中文
# DISPLAY = {"title": "标题", "abstract": "摘要", "source": "来源", "reference": "索引号", "condition": "申报条件", "standard": "扶持标准",
#            "issue": "发文号", "style": "文体", "level": "层级", "timeliness": "时效性", "stage": "政策阶段状态", "formality": "发文形式",
#            "effective": "有效年限", "write_time": "成文时间", "image": "标题图",
#            "publish_time": "发文时间", "effect_time": "生效时间", "invalid_time": "失效时间", "text": "正文", "address": "'机构地址",
#            "attachment": "附件（附件地址）", "main": "解读主题", "view": "浏览量", "author": "作者", "name": "机构名称",
#            "file": "全文下载", "keywords": "关键词", "introduce": "描述", "classification": "机构分类", "process": "办理流程",
#            "method": "申报方式", "requirement": "材料递交要求", "status": "申报状态", "special": "专项类型"
#            }


#在字段命名中，标题的字段名必须含有'title',正文的字段必须含有'text'，其他字段不能包含以上两字符串
DISPLAY = {"abstract": "摘要", "source": "来源", "reference": "索引号", "condition": "申报条件", "standard": "扶持标准",
           "issue": "发文号", "style": "文体", "level": "层级", "timeliness": "时效性", "stage": "政策阶段状态", "formality": "发文形式",
           "effective": "有效年限", "write_time": "成文时间", "image": "标题图",
           "publish_time": "发文时间", "effect_time": "生效时间", "invalid_time": "失效时间", "address": "机构地址",
           "attachment": "附件（附件地址）", "main": "解读主题", "view": "浏览量", "author": "作者", "name": "机构名称",
           "file": "全文下载", "keywords": "关键词", "introduce": "描述", "classification": "机构分类", "process": "办理流程",
           "method": "申报方式", "requirement": "材料递交要求", "status": "申报状态", "special": "专项类型"
           }

SETTING_FOR_GUOCE = True