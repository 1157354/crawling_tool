__author__ = 'tian'
from scrapy import cmdline

# cmdline.execute("scrapy crawl Tool".split())
# cmdline.execute("scrapy crawl content".split())
cmdline.execute(['scrapy', 'crawl', 'Tool', '-a', 'id=742'])