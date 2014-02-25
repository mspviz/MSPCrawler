# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class MSPItem(Item):
    # define the fields for your item here like:
    # name = Field()
    mspid = Field()
    name = Field()
    area = Field()
    parentregion = Field()
    email = Field()
    party = Field()
    imguri = Field()
    
class VoteItem(Item):
    mspid = Field()
    detail = Field()
    MSPVote = Field()
    result = Field()