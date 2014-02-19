MSPCrawler
==========

A scrapy crawler for MSP votes in the Scottish Parliament

Produces msps.json containing all current MSPs and their details and votes.json containing all votes cast with MSP ID and motion detail.

TODO:
- Handle EVENTVALIDATION errors (drops to debug atm)
- Grab motion/amendment ID from motion detail

Usage:
scrapy crawl msp --loglevel ERROR