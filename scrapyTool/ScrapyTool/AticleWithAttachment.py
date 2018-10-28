__author__ = 'tian'
import requests
import re
from scrapyTool.ScrapyTool.Article import Article
from app.setting import DOWNLOAD_LOCATION
import datetime


class ArticleWithAttachment(Article):
    def __init__(self, input, url=None, min_text_length=25, retry_length=250):
        super(ArticleWithAttachment, self).__init__(input, url, min_text_length, retry_length)

    def getArticleWithAttachment(self, response):
        myArticle = self.summary(html_partial=True)
        dict_file = self.dealWithText(myArticle, response)
        newText = self.textReedit(myArticle, dict_file)
        return newText

    def downloadFile(self, url, filename):
        r = requests.get(url)
        with open(DOWNLOAD_LOCATION + filename, 'wb') as f:
            f.write(r.content)

    def dealWithText(self, textXpath, response):
        # 处理以a标签开头的图片或者附件
        myRe = re.compile('<a.*?href="(.*?)".*?>')
        url_all = myRe.findall(textXpath)
        # print('url_all,', url_all)
        dict_file = {}
        if url_all is not None:
            for url in url_all:
                url = url.strip()
                if '/' in url:
                    filename = self.getTime()+'_'+url[(url.rindex('/') + 1):]
                else:
                    filename = self.getTime()+'_'+url
                if not url.endswith('html') and not url.endswith('htm'):

                    if url.endswith('jpg') or url.endswith('JPG') or url.endswith('png') or url.endswith('PNG'):
                        dict_file[url] = DOWNLOAD_LOCATION + filename
                        if not url.startswith('http'):
                            url = response.urljoin(url)
                        self.downloadFile(url, filename)
                    if url.endswith('doc') or url.endswith('zip') or url.endswith('docx') or url.endswith('pdf') or \
                            url.endswith('xls') or url.endswith('csv') or url.endswith('xlsx') or url.endswith('rar'):
                        dict_file[url] = DOWNLOAD_LOCATION + filename
                        if not url.startswith('http'):
                            url = response.urljoin(url)
                        self.downloadFile(url, filename)

        # 处理图片
        img_re = re.compile('<img.*?src="(.*?)".*?>')
        img_urls = img_re.findall(textXpath)
        if img_urls is not None:
            for img_url in img_urls:
                img_url = img_url.strip()
                if '/' in img_url:
                    img_name = self.getTime()+'_'+img_url[(img_url.rindex('/') + 1):]
                else:
                    img_name = self.getTime()+'_'+img_url
                dict_file[img_url] = DOWNLOAD_LOCATION + img_name
                img_url = response.urljoin(img_url)
                self.downloadFile(img_url, img_name)
        return dict_file

    def textReedit(self, text, dict_file):
        text_ = text
        for k in dict_file.keys():
            text_ = re.sub(k, dict_file.get(k), text)
            text = text_
        return text_

    def getTime(self):
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')



if __name__ == "__main__":
    pass
