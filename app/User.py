import json

class UserInfo(dict):
    __slots__ = ('user_id','website','table_name','default_crawl_flag','fields_xpath_list',
                 'two_or_three_mode','page_num','if_store_data','error_msg','url_list_xpath','page_num_list','crawling_result','spider_state')
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

    def to_json(self):
        return json.dumps(self)

    @classmethod
    def from_json(cls,json_data):
        if json_data:
            return cls(json.loads(json_data))
        else:
            raise ValueError('json_data should not be empty.')



class User:
    def __init__(self,user_id,website,table_name,default_crawl_flag,fields_xpath_list,
                 two_or_three_mode,page_num,if_store_data,error_msg):
        self._user_id = user_id
        self._website = website
        self._table_name = table_name
        self._default_crawl_flag = default_crawl_flag
        self._fields_xpath_list = fields_xpath_list
        self._two_or_three_mode = two_or_three_mode
        self._page_num = page_num
        self._if_store_data = if_store_data
        self._error_msg = error_msg

    def to_json(self):
        return json.dumps({'user_id':self._user_id,
                           'website':self._website,
                           'table_name':self._table_name,
                           'default_crawl_flag':self._default_crawl_flag,
                           'fields_xpath_list':self._fields_xpath_list,
                           'two_or_three_mode':self._two_or_three_mode,
                           'page_num':self._page_num,
                           'if_store_data':self._if_store_data,
                           'error_msg':self._error_msg})

    @classmethod
    def from_json(cls,json_data):
        return cls(json_data)

    @classmethod
    def get_data(cls):
        print(cls.user_id)


    @property
    def user_id(self):
        return self._user_id



    @property
    def website(self):
        return self._website
    @website.setter
    def website(self,value):
        self._website = value


    @property
    def table_name(self):
        return self._table_name
    @table_name.setter
    def table_name(self,value):
        self._table_name = value

    @property
    def default_crawl_flag(self):
        return self._dafault_crawl_flag
    @default_crawl_flag.setter
    def default_crawl_flag(self,value):
        self._default_crawl_flag = value

    @property
    def fields_xpath_list(self):
        return self._fields_xpath_list
    @fields_xpath_list.setter
    def fields_xpath_list(self,value):
        self._fields_xpath_list = value

    @property
    def two_or_three_mode(self):
        return self._two_or_three_mode
    @two_or_three_mode.setter
    def two_or_three_mode(self,value):
        self._two_or_three_mode = value

    @property
    def page_num(self):
        return self._page_num
    @page_num.setter
    def page_num(self,value):
        self._page_num = value

    @property
    def if_store_date(self):
        return self._if_store_data
    @if_store_date.setter
    def if_store_data(self,value):
        self._if_store_data = value

    @property
    def error_msg(self):
        return self._error_msg
    @error_msg.setter
    def error_msg(self,value):
        self._error_msg = value


if __name__ == '__main__':
    pass
