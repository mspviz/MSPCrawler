# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from msp.items import MSPItem, VoteItem
from scrapy import signals
from scrapy.contrib.exporter import JsonLinesItemExporter

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
        MSPFile = open('msps.json', 'w+b')
        self.files['msps'] = MSPFile
        self.MSPExporter = JsonLinesItemExporter(MSPFile)
        self.MSPExporter.start_exporting()
        
        VoteFile = open('votes.json', 'w+b')
        self.files['votes'] = VoteFile
        self.VoteExporter = JsonLinesItemExporter(VoteFile)
        self.VoteExporter.start_exporting()
        
    def spider_closed(self, spider):
        self.VoteExporter.finish_exporting()
        self.MSPExporter.finish_exporting()
        for file in self.files.values():
            file.close()
    
    def process_item(self, item, spider):
        if isinstance(item, MSPItem):
            self.MSPExporter.export_item(item)
        elif isinstance(item, VoteItem):
            self.VoteExporter.export_item(item)
        return item
