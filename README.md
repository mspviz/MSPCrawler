MSPCrawler
==========

A scrapy crawler for MSP votes in the Scottish Parliament

Produces msps.json containing all current MSPs and their details and votes.json containing all votes cast with MSP ID and motion detail. Votes are crawled separately for each MSP, use the getAllVotes.py helper script to crawl every MP.

TODO:
- Grab motion/amendment ID from motion detail
- Handle missing table pagination row

Usage:

    scrapy crawl msps
    scrapy crawl votes -a mspid=THEMSPID

Alternatively, for all votes:

    scrapy crawl msps
    python getAllVotes.py
