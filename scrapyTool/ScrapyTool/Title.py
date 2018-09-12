__author__ = 'tian'
import re
import lxml.html
from lxml.etree import tostring
from scrapyTool.ScrapyTool.Document import Document
# from .Document import Document

class Title(Document):
    def __init__(self,input,url=None,min_text_length=25,retry_length=250):
        super().__init__(input,url,min_text_length,retry_length)
        self.TITLE_CSS_HEURISTICS = ['#title', '#head', '#heading', '.pageTitle',
                        '.news_title', '.title', '.head', '.heading',
                        '.contentheading', '.small_header_red']

    def normalize_spaces(self,s):
        if not s:
            return ''
        return ' '.join(s.split())

    def build_doc(self,page):
        doc = lxml.html.document_fromstring(page,parser=lxml.html.HTMLParser(encoding='utf-8'))
        return doc



    def normalize_entities(self,cur_title):
        entities = {
            u'\u2014':'-',
            u'\u2013':'-',
            u'&mdash;': '-',
            u'&ndash;': '-',
            u'\u00A0': ' ',
            u'\u00AB': '"',
            u'\u00BB': '"',
            u'&quot;': '"',
        }
        for c, r in entities.items():
            if c in cur_title:
                cur_title = cur_title.replace(c, r)
        return cur_title

    def norm_title(self,title):
        return self.normalize_entities(self.normalize_spaces(title))

    def get_title(self,doc):
        title = doc.find('.//title')
        if title is None or title.text is None or len(title.text) == 0:
            return '[no-title]'

        return self.norm_title(title.text)

    def add_match(self,collection, text, orig):
        text = self.norm_title(text)
        if len(text.split()) >= 2 and len(text) >= 15:
            if text.replace('"', '') in orig.replace('"', ''):
                collection.add(text)

    def shorten_title(self,doc):
        title = doc.find('.//title')
        if title is None or title.text is None or len(title.text) == 0:
            return ''

        title = orig = self.norm_title(title.text)

        candidates = set()

        for item in ['.//h1', './/h2', './/h3']:
            for e in list(doc.iterfind(item)):
                if e.text:
                    self.add_match(candidates, e.text, orig)
                if e.text_content():
                    self.add_match(candidates, e.text_content(), orig)

        for item in self.TITLE_CSS_HEURISTICS:
            for e in doc.cssselect(item):
                if e.text:
                    self.add_match(candidates, e.text, orig)
                if e.text_content():
                    self.add_match(candidates, e.text_content(), orig)

        if candidates:
            title = sorted(candidates, key=len)[-1]
        else:
            for delimiter in [' | ', ' - ', ' :: ', ' / ']:
                if delimiter in title:
                    parts = orig.split(delimiter)
                    if len(parts[0].split()) >= 4:
                        title = parts[0]
                        break
                    elif len(parts[-1].split()) >= 4:
                        title = parts[-1]
                        break
            else:
                if ': ' in title:
                    parts = orig.split(': ')
                    if len(parts[-1].split()) >= 4:
                        title = parts[-1]
                    else:
                        title = orig.split(': ', 1)[1]

        if not 15 < len(title) < 150:
            return orig

        return title

    def short_title(self):
        return self.shorten_title(self.html)

if __name__ == '__main__':
    url = 'http://www.chinasafety.gov.cn/xw/byw/201807/t20180731_219151.shtml'
    import urllib.request,urllib.parse,urllib.error
    request = urllib.request.Request(url)
    file = urllib.request.urlopen(request)
    doc = Title(file.read().decode('utf-8'),url=url)
    # doc._html()
    result = doc.short_title()
    print(result)