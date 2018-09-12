__author__ = 'tian'

from lxml.html.clean import Cleaner
import lxml.html
import re


class Document(object):
    def __init__(self, input, url=None, min_text_length=25, retry_length=250):
        self.html_cleaner = Cleaner(scripts=True, javascript=True, comments=True,
                                    style=True, links=True, meta=False, add_nofollow=False,
                                    page_structure=False, processing_instructions=True, embedded=False,
                                    frames=False, forms=False, annoying_tags=False, remove_tags=None,
                                    remove_unknown_tags=False, safe_attrs_only=False)
        self.input = input
        # self.html = None
        self.html = self._html()
        self.encoding = None
        self.url = url
        self.min_text_length = min_text_length
        self.retry_length = retry_length
        self.uids = {}
        self.uids_document = None

        self.bad_attrs = ['width', 'height', 'style', '[-a-z]*color', 'background[-a-z]*', 'on*']
        self.single_quoted = "'[^']+'"
        self.double_quoted = '"[^"]+"'
        self.non_space = '[^ "\'>]+'
        self.htmlstrip = re.compile("<"  # open
                                    "([^>]+) "  # prefix
                                    "(?:%s) *" % ('|'.join(self.bad_attrs),) +  # undesirable attributes
                                    '= *(?:%s|%s|%s)' % (
                                    self.non_space, self.single_quoted, self.double_quoted) +  # value
                                    "([^>]*)"  # postfix
                                    ">"  # end
                                    , re.I)

    def build_doc(self, page):
        doc = lxml.html.document_fromstring(page, parser=lxml.html.HTMLParser(encoding='utf-8'))
        return doc

    def _parse(self, input):
        # 没有执行url的校验
        doc = self.build_doc(input)
        doc = self.html_cleaner.clean_html(doc)
        return doc

    def _html(self):
        # if self.html is None:
        #     self.html = self._parse(self.input)
        self.html = self._parse(self.input)
        return self.html

    def describe_node(self, node):

        if node is None:
            return ''
        if not hasattr(node, 'tag'):
            return "[%s]" % type(node)
        name = node.tag
        if node.get('id', ''):
            name += '#' + node.get('id')
        if node.get('class', '').strip():
            name += '.' + '.'.join(node.get('class').split())
        if name[:4] in ['div#', 'div.']:
            name = name[3:]
        if name in ['tr', 'td', 'div', 'p']:
            uid = self.uids.get(node)
            if uid is None:
                uid = self.uids[node] = len(self.uids) + 1
            name += "{%02d}" % uid
        return name

    def describe(self, node, depth=1):
        doc = node.getroottree().getroot()
        if doc != self.uids_document:
            self.uids = {}
            self.uids_document = doc
        parent = ''
        if depth and node.getparent() is not None:
            parent = self.describe(node.getparent(), depth=depth - 1) + '>'
        return parent + self.describe_node(node)

    def text_content(self, elem, length=40):
        RE_COLLAPSE_WHITESPACES = re.compile('\s+', re.U)
        content = RE_COLLAPSE_WHITESPACES.sub(' ', elem.text_content().replace('\r', ''))
        if len(content) < length:
            return content
        return content[:length] + '...'
