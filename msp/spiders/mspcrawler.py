from scrapy.spider import Spider
from scrapy.selector import Selector
from msp.items import MSPItem, VoteItem
from scrapy.http import Request, Response
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc
from scrapy.http import FormRequest
from scrapy.shell import inspect_response
import re

class VoteCrawler(Spider):
    name = "votes"
    allowed_domains = ["scottish.parliament.uk"]
    start_urls = ["http://www.scottish.parliament.uk/parliamentarybusiness/28925.aspx"]
    
    def __init__(self, mspid=None, *args, **kwargs):
        super(VoteCrawler, self).__init__(*args, **kwargs)
        if not mspid:
            raise Error
        self.mspid = mspid
    
    def parse(self, response):
        sel = Selector(response)
        yield FormRequest.from_response(response, callback=self.parseVoteSearchResults, formdata={'SelectVoteHistoryView$btnSearch':'Search','SelectVoteHistoryView$ddlMSP':str(self.mspid)}, meta={'fetch':True})
        
    def parseVoteSearchResults(self, response):
        sel = Selector(response)
        
        validationstr = self.getValidationString(response)
        
        # Parse the first page of results
        for voteItem in self.parseVoteTableResults(response):
            yield voteItem
        
        pages = 1
        
        # Grab the vote table
        voteTable = sel.css('#SelectVoteHistoryView_GridView1')
        rows = voteTable.css('tr')
        
        # The last row contains the page links
        paginationRow = rows[-1]
        
        firstCellElement = paginationRow.css('td>span::text')
        if not firstCellElement:
            # Can't find the navigate bar??
            return
        firstCellContent = firstCellElement.extract()[0]
        
        # Check if there are any pages..
        if str(firstCellContent).isdigit():
            thisPage = int(firstCellContent)-1
            
            # The last cell contains some js to skip to the final page
            lastCell = paginationRow.css('td')[-1]
            lastPageElem = lastCell.css('a::attr(onclick)')
            if len(lastPageElem) != 1:
                # We're on the last set of pages, so there's no last page link
                return
            
            lastPageLink = lastPageElem[0].extract()
    
            # Need to pull page number out of this: javascript:__gvSelectVoteHistoryView_GridView1.callback("69|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=|"); return false;
            # It's the first value in the param string
            # TODO: Error handling...
            pages = int(re.split('\"|\|',lastPageLink)[1]) + 1
            
            # Only iterate over pages if this is a new table
            if response.meta['fetch']:
                for i in range(thisPage,min([pages,thisPage+11])):
                    fetch = False
                    if i == thisPage + 10:
                        fetch = True

                    if validationstr:
                        # The fact we have a validationstr means we need a surrogate form (this is a callback)
                        form = response.meta['form']
                        yield FormRequest.from_response(form, callback=self.parseVoteSearchResults, formdata={'__CALLBACKID':'SelectVoteHistoryView$GridView1',
                                                                                                       '__CALLBACKPARAM':str(i)+'|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=||' + str(thisPage) + '|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=|/wFk7SDVa18iduwa7ivhFHIM55t+AhI=',
                                                                                                        '__EVENTVALIDATION':validationstr},meta={'fetch':fetch,'form':form})
                    else:
                        # Should only get here if this is first page
                        #inspect_response(response)
                        yield FormRequest.from_response(response, callback=self.parseVoteSearchResults, formdata={'__CALLBACKID':'SelectVoteHistoryView$GridView1',
                                                                                                       '__CALLBACKPARAM':str(i)+'|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=||' + str(thisPage) + '|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=|/wFk7SDVa18iduwa7ivhFHIM55t+AhI='},meta={'fetch':fetch,'form':response})
                
    def parseVoteTableResults(self, response):
        sel = Selector(response)

        # Grab the vote table
        voteTable = sel.css('#SelectVoteHistoryView_GridView1')
        rows = voteTable.css('tr')
                
        #Get each vote result
        for r in rows:
            VoteInfo = VoteItem()
            # Check if a vote result
            voteDetail = r.css('td > span::text').extract()
            if len(voteDetail) != 1: continue
            
            VoteInfo['detail'] = voteDetail[0]
            VoteInfo['mspid'] = self.mspid
            
            cells = r.css('td::text').extract()
            if len(cells) == 2:
                VoteInfo['MSPVote'] = cells[0]
                VoteInfo['result'] = cells[1]
                
                # TODO: Grab the full voteDetail..
                yield VoteInfo
    
    def getValidationString(self, response):
        responseTest = response._body[:12]
        pos = responseTest.find('|')
        validationstr = ''
        if pos != -1:
            # This is from a callback, we need to update EVENTVALIDATION
            validationLength = int(response._body[:pos])
            validationstr = response._body[pos+1:pos+1+validationLength]
            return validationstr
        else:
            return None

class MSPCrawler(Spider):
    name = "msps"
    allowed_domains = ["scottish.parliament.uk"]
    start_urls = ["http://www.scottish.parliament.uk/msps/177.aspx"]
    
    def parse(self, response):        
        sel = Selector(response)
        
        # Get the list element for each MSP, but not descendants
        mspsList = sel.css('.alphabetListDetails > ul > li')
        
        for msp in mspsList:
            MSPInfo = MSPItem()
            # Name and Area are in bold
            MSPInfo['name'], MSPInfo['area'] = [e.strip() for e in msp.css('strong::text').extract()]
            linkthru, MSPInfo['email'] = msp.css('a::attr(href)').extract()
            MSPInfo['imguri'] = URL = urljoin_rfc(get_base_url(response),msp.css('img::attr(src)')[0].extract())
            # Party affiliation is first <p> within the alphabetListItem container
            MSPInfo['party'] = msp.css('.alphabetListItem p::text').extract()[0].strip()
            
            URL = urljoin_rfc(get_base_url(response),linkthru)
            yield Request(URL, self.parseMSP, meta={"MSP":MSPInfo})
            
    def parseMSP(self, response):           
        sel = Selector(response)
        MSPInfo = response.meta["MSP"]
        
        # Opportunity to grab more detailed MSP info e.g. website, twitter
        # For example, local MSPS have their parent region after a bold field containg 'Region'
        region = sel.xpath("//strong[contains(., 'Region')]/following-sibling::text()")
        if region:
            MSPInfo['parentregion'] = region[0].extract()[1:]
        
        linkthru = sel.css('#recentVoting_hlkAdvancedSearch::attr(href)').extract()[0]
        MSPInfo['mspid'] = re.split('m=',linkthru)[-1]
        
        yield MSPInfo
        
        # Broken off into separate crawler!
        #URL = urljoin_rfc(get_base_url(response), linkthru)
        
        #yield Request(URL, self.parseVoteSearchForm, meta=response.meta)