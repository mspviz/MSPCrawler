from scrapy.spider import Spider
from scrapy.selector import Selector
from msp.items import MSPItem, VoteItem
from scrapy.http import Request, Response
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc
from scrapy.http import FormRequest
from scrapy.shell import inspect_response
import re

class MSPCrawler(Spider):
    name = "msp"
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
        
        linkthru = sel.css('#recentVoting_hlkAdvancedSearch::attr(href)').extract()[0]
        MSPInfo['mspid'] = re.split('m=',linkthru)[-1]
        
        yield MSPInfo
        
        URL = urljoin_rfc(get_base_url(response), linkthru)
        
        yield Request(URL, self.parseVoteSearchForm, meta=response.meta)

    def parseVoteSearchForm(self, response):       
        # Auto-fill the vote search form and fetch results
        yield FormRequest.from_response(response, callback=self.parseVoteSearchResults, formdata={'SelectVoteHistoryView$btnSearch':'Search'}, meta=response.meta)
        
    def parseVoteSearchResults(self, response):
        # Get the pagination from the table
        pages = self.parseVoteTablePagination(response)
        
        # Parse the first page of results
        for voteItem in self.parseVoteTableResults(response):
            yield voteItem
            
        # TODO: handle each available page link concurrently using this __EVENTVALIDATION string
        # rather than getting one which grows each time
            
        # Move onto page 2
        response.meta['page'] = 1
        response.meta['pagecount'] = pages
        response.meta['form'] = response
        
        # The remaining pages are dealt with using callbacks (the site handles these in JS)
        yield FormRequest.from_response(response, callback=self.parseVoteTableCallback, formdata={'__CALLBACKID':'SelectVoteHistoryView$GridView1',
                                                                                               '__CALLBACKPARAM':str(response.meta['page'])+'|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=||' + str(response.meta['page']-1) + '|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=|/wFk7SDVa18iduwa7ivhFHIM55t+AhI='},meta=response.meta)
        
    def parseVoteTableResults(self, response):
        sel = Selector(response)
        MSPInfo = response.meta["MSP"]

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
            VoteInfo['mspid'] = MSPInfo['mspid']
            
            cells = r.css('td::text').extract()
            if len(cells) == 2:
                VoteInfo['MSPVote'] = cells[0]
                VoteInfo['result'] = cells[1]
                
                # TODO: Grab the full voteDetail..
                yield VoteInfo
        
    def parseVoteTablePagination(self, response):
        sel = Selector(response)
        
        # Grab the vote table
        voteTable = sel.css('#SelectVoteHistoryView_GridView1')
        rows = voteTable.css('tr')
        
        # The last row contains the page links
        paginationRow = rows[-1]
        
        firstCellContent = paginationRow.css('td>span::text').extract()[0]
        if firstCellContent != '1':
            # This is the only page!
            return 1
        
        # The last cell contains some js to skip to the final page
        lastCell = paginationRow.css('td')[-1]
        lastPageLink = lastCell.css('a::attr(onclick)')[0].extract()

        # Need to pull page number out of this: javascript:__gvSelectVoteHistoryView_GridView1.callback("69|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=|"); return false;
        # It's the first value in the param string
        # TODO: Error handling...
        lastPageNum = int(re.split('\"|\|',lastPageLink)[1]) + 1
        return lastPageNum
           
    def parseVoteTableCallback(self, response):
        form = response.meta['form']
        
        #inspect_response(response)
        
        # Check if we got some EVENTVALIDATION data in the response
        responseTest = response._body[:12]
        pos = responseTest.find('|')
        validationstr = ''
        if pos != -1:
            # This is from a callback, we need to update EVENTVALIDATION
            validationLength = int(response._body[:pos])
            validationstr = response._body[pos+1:pos+1+validationLength]
        else:
            # Without a validationstr we'll just get sent back to page 1
            print "wtf"
            inspect_response(response)
            return
        
        for voteItem in self.parseVoteTableResults(response):
            yield voteItem
                
        # POST request for the next page of the table
        # Response contains new table, which we parse the results of
        # We need the event validation from this response, but the form from the first..
        # TODO: check callback isn't erroring and giving first page again!!
        response.meta['page'] += 1
        if response.meta['page'] < response.meta['pagecount']:
            yield FormRequest.from_response(form, callback=self.parseVoteTableCallback, formdata={'__CALLBACKID':'SelectVoteHistoryView$GridView1',
                                                                                               '__CALLBACKPARAM':str(response.meta['page'])+'|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=||' + str(response.meta['page']-1) + '|0|/wFlpZg1Fw7NYQJzL0vuw+Y57ZPx1ug=|/wFk7SDVa18iduwa7ivhFHIM55t+AhI=',
                                                                                               '__EVENTVALIDATION':validationstr},meta=response.meta)