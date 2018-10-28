__author__ = 'tian'
import re
import logging
from lxml.etree import tostring
from lxml.etree import tounicode
from scrapyTool.ScrapyTool.Document import Document
from lxml.html import document_fromstring
from lxml.html import fragment_fromstring

class Article(Document):
    def __init__(self,input,url=None,min_text_length=25,retry_length=250):
        super(Article,self).__init__(input,url,min_text_length,retry_length)
        self.REGEXES = {
            'unlikelyCandidatesRe': re.compile('combx|comment|community|disqus|extra|foot|header|menu|remark|rss|shoutbox|sidebar|sponsor|ad-break|agegate|pagination|pager|popup|tweet|twitter', re.I),
            'okMaybeItsACandidateRe': re.compile('and|article|body|column|main|shadow', re.I),
            'positiveRe': re.compile('article|body|content|entry|hentry|main|page|pagination|post|text|blog|story', re.I),
            'negativeRe': re.compile('combx|comment|com-|contact|foot|footer|footnote|masthead|media|meta|outbrain|promo|related|scroll|shoutbox|sidebar|sponsor|shopping|tags|tool|widget', re.I),
            'divToPElementsRe': re.compile('<(a|blockquote|dl|div|img|ol|p|pre|table|ul)', re.I),
            'videoRe': re.compile('https?:\/\/(www\.)?(youtube|vimeo)\.com', re.I),
        }
        self.log = logging.getLogger('mylog')



    def clean(self,text):
        text = re.sub('\s*\n\s*', '\n', text)
        text = re.sub('\t|[ \t]{2,}', ' ', text)
        return text.strip()

    def text_length(self,i):
        return len(self.clean(i.text_content() or ""))

    def get_body(self,doc):
        # for elem in doc.xpath('.//script | .//link'):
        for elem in doc.xpath('.//script | .//link | .//style'):
            elem.drop_tree()
        raw_html = str(tostring(doc.body or doc))
        cleaned = self.clean_attributes(raw_html)
        try:
            return cleaned
        except Exception:
            return raw_html

    def content(self):
        """Returns document body"""
        return self.get_body(self._html(True))

    def clean_attributes(self,html):
        while self.htmlstrip.search(html):
            html = self.htmlstrip.sub('<\\1\\2>', html)
        return html

    def get_clean_html(self):
        """
        An internal method, which can be overridden in subclasses, for example,
        to disable or to improve DOM-to-text conversion in .summary() method
        """
        return self.clean_attributes(tounicode(self.html))

    def select_best_candidate(self, candidates):
        if not candidates:
            return None

        sorted_candidates = sorted(
            candidates.values(),
            key=lambda x: x['content_score'],
            reverse=True
        )
        for candidate in sorted_candidates[:5]:
            elem = candidate['elem']
            # self.log.info("Top 5 : %6.3f %s" % (
            #     candidate['content_score'],
            #     self.describe(elem)))

        best_candidate = sorted_candidates[0]
        return best_candidate

    def get_link_density(self, elem):
        link_length = 0
        for i in elem.findall(".//a"):
            link_length += self.text_length(i)
        #if len(elem.findall(".//div") or elem.findall(".//p")):
        #    link_length = link_length
        total_length = self.text_length(elem)
        return float(link_length) / max(total_length, 1)

    def score_paragraphs(self):
        MIN_LEN = self.min_text_length
        candidates = {}
        ordered = []
        for elem in self.tags(self._html(), "p", "pre", "td"):
            parent_node = elem.getparent()
            if parent_node is None:
                continue
            grand_parent_node = parent_node.getparent()

            inner_text = self.clean(elem.text_content() or "")
            inner_text_len = len(inner_text)

            # If this paragraph is less than 25 characters
            # don't even count it.
            if inner_text_len < MIN_LEN:
                continue

            if parent_node not in candidates:
                candidates[parent_node] = self.score_node(parent_node)
                ordered.append(parent_node)

            if grand_parent_node is not None and grand_parent_node not in candidates:
                candidates[grand_parent_node] = self.score_node(
                    grand_parent_node)
                ordered.append(grand_parent_node)

            content_score = 1
            content_score += len(inner_text.split(','))
            content_score += min((inner_text_len / 100), 3)
            #if elem not in candidates:
            #    candidates[elem] = self.score_node(elem)

            #WTF? candidates[elem]['content_score'] += content_score
            candidates[parent_node]['content_score'] += content_score
            if grand_parent_node is not None:
                candidates[grand_parent_node]['content_score'] += content_score / 2.0

        # Scale the final candidates score based on link density. Good content
        # should have a relatively small link density (5% or less) and be
        # mostly unaffected by this operation.
        for elem in ordered:
            candidate = candidates[elem]
            ld = self.get_link_density(elem)
            score = candidate['content_score']
            # self.log.debug("Branch %6.3f %s link density %.3f -> %6.3f" % (
            #     score,
            #     self.describe(elem),
            #     ld,
            #     score * (1 - ld)))
            candidate['content_score'] *= (1 - ld)

        return candidates

    def class_weight(self, e):
        weight = 0
        for feature in [e.get('class', None), e.get('id', None)]:
            if feature:
                if self.REGEXES['negativeRe'].search(feature):
                    weight -= 25

                if self.REGEXES['positiveRe'].search(feature):
                    weight += 25
        return weight

    def score_node(self, elem):
        content_score = self.class_weight(elem)
        name = elem.tag.lower()
        if name in ["div", "article"]:
            content_score += 5
        elif name in ["pre", "td", "blockquote"]:
            content_score += 3
        elif name in ["address", "ol", "ul", "dl", "dd", "dt", "li", "form", "aside"]:
            content_score -= 3
        elif name in ["h1", "h2", "h3", "h4", "h5", "h6", "th", "header", "footer", "nav"]:
            content_score -= 5
        return {
            'content_score': content_score,
            'elem': elem
        }

    def remove_unlikely_candidates(self):
        for elem in self.html.findall('.//*'):
            s = "%s %s" % (elem.get('class', ''), elem.get('id', ''))
            if len(s) < 2:
                continue
            if self.REGEXES['unlikelyCandidatesRe'].search(s) and (not self.REGEXES['okMaybeItsACandidateRe'].search(s)) and elem.tag not in ['html', 'body']:
                # self.log.debug("Removing unlikely candidate - %s" % self.describe(elem))
                elem.drop_tree()

    def transform_misused_divs_into_paragraphs(self):
        for elem in self.tags(self.html, 'div'):
            # transform <div>s that do not contain other block elements into
            # <p>s
            #FIXME: The current implementation ignores all descendants that
            # are not direct children of elem
            # This results in incorrect results in case there is an <img>
            # buried within an <a> for example
            if not self.REGEXES['divToPElementsRe'].search(
                    str(b''.join(map(tostring, list(elem))))):
                #log.debug("Altering %s to p" % (describe(elem)))
                elem.tag = "p"
                #print "Fixed element "+describe(elem)

        for elem in self.tags(self.html, 'div'):
            if elem.text and elem.text.strip():
                p = fragment_fromstring('<p/>')
                p.text = elem.text
                elem.text = None
                elem.insert(0, p)
                #print "Appended "+tounicode(p)+" to "+describe(elem)

            for pos, child in reversed(list(enumerate(elem))):
                if child.tail and child.tail.strip():
                    p = fragment_fromstring('<p/>')
                    p.text = child.tail
                    child.tail = None
                    elem.insert(pos + 1, p)
                    #print "Inserted "+tounicode(p)+" to "+describe(elem)
                if child.tag == 'br':
                    #print 'Dropped <br> at '+describe(elem)
                    child.drop_tree()

    def tags(self, node, *tag_names):
        for tag_name in tag_names:
            for e in node.findall('.//%s' % tag_name):
                yield e

    def reverse_tags(self, node, *tag_names):
        for tag_name in tag_names:
            for e in reversed(node.findall('.//%s' % tag_name)):
                yield e

    def sanitize(self, node, candidates):
        MIN_LEN = self.min_text_length
        for header in self.tags(node, "h1", "h2", "h3", "h4", "h5", "h6"):
            if self.class_weight(header) < 0 or self.get_link_density(header) > 0.33:
                header.drop_tree()

        for elem in self.tags(node, "form", "textarea"):
            elem.drop_tree()

        for elem in self.tags(node, "iframe"):
            if "src" in elem.attrib and self.REGEXES["videoRe"].search(elem.attrib["src"]):
                elem.text = "VIDEO" # ADD content to iframe text node to force <iframe></iframe> proper output
            else:
                elem.drop_tree()

        allowed = {}
        # Conditionally clean <table>s, <ul>s, and <div>s
        for el in self.reverse_tags(node, "table", "ul", "div", "aside", "header", "footer", "section"):
            if el in allowed:
                continue
            weight = self.class_weight(el)
            if el in candidates:
                content_score = candidates[el]['content_score']
                #print '!',el, '-> %6.3f' % content_score
            else:
                content_score = 0
            tag = el.tag

            if weight + content_score < 0:
                # self.log.debug("Removed %s with score %6.3f and weight %-3s" %
                #     (self.describe(el), content_score, weight, ))
                el.drop_tree()
            elif el.text_content().count(",") < 10:
                counts = {}
                for kind in ['p', 'img', 'li', 'a', 'embed', 'input']:
                    counts[kind] = len(el.findall('.//%s' % kind))
                counts["li"] -= 100
                counts["input"] -= len(el.findall('.//input[@type="hidden"]'))

                # Count the text length excluding any surrounding whitespace
                content_length = self.text_length(el)
                link_density = self.get_link_density(el)
                parent_node = el.getparent()
                if parent_node is not None:
                    if parent_node in candidates:
                        content_score = candidates[parent_node]['content_score']
                    else:
                        content_score = 0
                #if parent_node is not None:
                    #pweight = self.class_weight(parent_node) + content_score
                    #pname = describe(parent_node)
                #else:
                    #pweight = 0
                    #pname = "no parent"
                to_remove = False
                reason = ""

                #if el.tag == 'div' and counts["img"] >= 1:
                #    continue
                if counts["p"] and counts["img"] > 1+counts["p"]*1.3:
                    reason = "too many images (%s)" % counts["img"]
                    to_remove = True
                elif counts["li"] > counts["p"] and tag != "ul" and tag != "ol":
                    reason = "more <li>s than <p>s"
                    to_remove = True
                elif counts["input"] > (counts["p"] / 3):
                    reason = "less than 3x <p>s than <input>s"
                    to_remove = True
                elif content_length < MIN_LEN and counts["img"] == 0:
                    reason = "too short content length %s without a single image" % content_length
                    to_remove = True
                elif content_length < MIN_LEN and counts["img"] > 2:
                    reason = "too short content length %s and too many images" % content_length
                    to_remove = True
                elif weight < 25 and link_density > 0.2:
                        reason = "too many links %.3f for its weight %s" % (
                            link_density, weight)
                        to_remove = True
                elif weight >= 25 and link_density > 0.5:
                    reason = "too many links %.3f for its weight %s" % (
                        link_density, weight)
                    to_remove = True
                elif (counts["embed"] == 1 and content_length < 75) or counts["embed"] > 1:
                    reason = "<embed>s with too short content length, or too many <embed>s"
                    to_remove = True
                elif not content_length:
                    reason = "no content"
                    to_remove = True

                    i, j = 0, 0
                    x = 1
                    siblings = []
                    for sib in el.itersiblings():
                        #log.debug(sib.text_content())
                        sib_content_length = self.text_length(sib)
                        if sib_content_length:
                            i =+ 1
                            siblings.append(sib_content_length)
                            if i == x:
                                break
                    for sib in el.itersiblings(preceding=True):
                        #log.debug(sib.text_content())
                        sib_content_length = self.text_length(sib)
                        if sib_content_length:
                            j =+ 1
                            siblings.append(sib_content_length)
                            if j == x:
                                break
                    #log.debug(str_(siblings))
                    if siblings and sum(siblings) > 1000:
                        to_remove = False
                        self.log.debug("Allowing %s" % self.describe(el))
                        for desnode in self.tags(el, "table", "ul", "div", "section"):
                            allowed[desnode] = True

                if to_remove:
                    # self.log.debug("Removed %6.3f %s with weight %s cause it has %s." %
                    #     (content_score, self.describe(el), weight, reason))
                    #print tounicode(el)
                    #log.debug("pname %s pweight %.3f" %(pname, pweight))
                    el.drop_tree()
                else:
                    self.log.debug("Not removing %s of length %s: %s" % (
                        self.describe(el), content_length, self.text_content(el)))

        self.html = node
        return self.get_clean_html()

    def get_article(self, candidates, best_candidate, html_partial=False):
        # Now that we have the top candidate, look through its siblings for
        # content that might also be related.
        # Things like preambles, content split by ads that we removed, etc.
        sibling_score_threshold = max([
            10,
            best_candidate['content_score'] * 0.2])
        # create a new html document with a html->body->div
        if html_partial:
            output = fragment_fromstring('<div/>')
        else:
            output = document_fromstring('<div/>')
        best_elem = best_candidate['elem']
        parent = best_elem.getparent()
        siblings = parent.getchildren() if parent is not None else [best_elem]
        for sibling in siblings:
            # in lxml there no concept of simple text
            # if isinstance(sibling, NavigableString): continue
            append = False
            if sibling is best_elem:
                append = True
            sibling_key = sibling  # HashableElement(sibling)
            if sibling_key in candidates and \
                candidates[sibling_key]['content_score'] >= sibling_score_threshold:
                append = True

            if sibling.tag == "p":
                link_density = self.get_link_density(sibling)
                node_content = sibling.text or ""
                node_length = len(node_content)

                if node_length > 80 and link_density < 0.25:
                    append = True
                elif node_length <= 80 \
                    and link_density == 0 \
                    and re.search('\.( |$)', node_content):
                    append = True

            if append:
                # We don't want to append directly to output, but the div
                # in html->body->div
                if html_partial:
                    output.append(sibling)
                else:
                    output.getchildren()[0].getchildren()[0].append(sibling)
        #if output is not None:
        #    output.append(best_elem)
        return output

    def summary(self, html_partial=False):
        """
        Given a HTML file, extracts the text of the article.

        :param html_partial: return only the div of the document, don't wrap
        in html and body tags.

        Warning: It mutates internal DOM representation of the HTML document,
        so it is better to call other API methods before this one.
        """
        try:
            ruthless = True
            while True:
                self._html()
                for i in self.tags(self.html, 'script'):
                # for i in self.tags(self.html, 'script', 'style'):
                    i.drop_tree()
                for i in self.tags(self.html, 'body'):
                    i.set('id', 'readabilityBody')
                if ruthless:
                    self.remove_unlikely_candidates()
                #有待检查和进一步了解
                self.transform_misused_divs_into_paragraphs()
                candidates = self.score_paragraphs()

                best_candidate = self.select_best_candidate(candidates)

                if best_candidate:
                    article = self.get_article(candidates, best_candidate,
                            html_partial=html_partial)
                else:
                    if ruthless:
                        self.log.info("ruthless removal did not work. ")
                        ruthless = False
                        self.log.debug(
                            ("ended up stripping too much - "
                             "going for a safer _parse"))
                        # try again
                        continue
                    else:
                        self.log.debug(
                            ("Ruthless and lenient parsing did not work. "
                             "Returning raw html"))
                        article = self.html.find('body')
                        if article is None:
                            article = self.html
                cleaned_article = self.sanitize(article, candidates)

                article_length = len(cleaned_article or '')
                retry_length = self.retry_length
                of_acceptable_length = article_length >= retry_length
                if ruthless and not of_acceptable_length:
                    ruthless = False
                    # Loop through and try again.
                    continue
                else:
                    return cleaned_article
        except Exception as e:
            self.log.exception('error getting summary: ')


if __name__ == "__main__":
    # url = 'http://www.chinasafety.gov.cn/xw/byw/201807/t20180731_219151.shtml'
    url = 'http://www.chinalaw.gov.cn/art/2018/4/8/art_12_207841.html'
    import urllib.request,urllib.parse,urllib.error
    request = urllib.request.Request(url)
    file = urllib.request.urlopen(request)
    doc = Article(file.read().decode('utf-8'),url=url)
    doc._html()
    result = doc.summary()
    print(result)