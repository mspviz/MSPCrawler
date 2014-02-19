# Scrapy settings for msp project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'msp'

SPIDER_MODULES = ['msp.spiders']
NEWSPIDER_MODULE = 'msp.spiders'
ITEM_PIPELINES = {
    'msp.pipelines.MspPipeline': 100,
}

RETRY_ENABLED = True
RETRY_TIMES = 5

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'msp (+http://www.yourdomain.com)'
# MSP Site doesn't give us the js onclick without a recognised user agent
USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36"

LOG_ENABLED = False
# Politeness vs. speed
CONCURRENT_REQUESTS_PER_IP = 8