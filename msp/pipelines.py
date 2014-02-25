# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from msp.items import MSPItem, VoteItem
from msp.spiders.mspcrawler import MSPCrawler, VoteCrawler
from scrapy import signals
from scrapy.contrib.exporter import JsonLinesItemExporter
import os

class MspPipeline(object):
    def __init__(self):
        self.files = {}
        self.ids_seen = set()
    
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline
    
    def spider_opened(self, spider):
        if not os.path.exists('./json/'):
            os.makedirs('./json/')
        if isinstance(spider, MSPCrawler):
            MSPFile = open('json/msps.json', 'w+b')
            self.files['msps'] = MSPFile
            self.MSPExporter = JsonLinesItemExporter(MSPFile)
            self.MSPExporter.start_exporting()
        elif isinstance(spider, VoteCrawler):
            VoteFile = open('json/votes-' + spider.mspid + '.json', 'w+b')
            self.files['votes'] = VoteFile
            self.VoteExporter = JsonLinesItemExporter(VoteFile)
            self.VoteExporter.start_exporting()
        
    def spider_closed(self, spider):
        if isinstance(spider, VoteCrawler):
            self.VoteExporter.finish_exporting()
        elif isinstance(spider, MSPCrawler):
            self.MSPExporter.finish_exporting()
        for file in self.files.values():
            file.close()
    
    def process_item(self, item, spider):
        if isinstance(item, MSPItem):
            self.MSPExporter.export_item(item)
        elif isinstance(item, VoteItem):
            self.VoteExporter.export_item(item)
        return item
