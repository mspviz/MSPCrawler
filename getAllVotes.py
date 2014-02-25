import json
import subprocess

def mergeVotes():
    from os import listdir
    from os.path import isfile, join
    
    with file('json/votes.json','w') as w:
        for fs in listdir('./json'):
            fp = join('./json',fs)
            if isfile(fp) and fs.startswith('votes-'):
                with file(fp,'r') as f:
                    w.write(f.read())
    print "Votes merged!"

with file('json/msps.json','r') as f:
    for line in f:
        msp = json.loads(line)
        print msp['name']
        # Run scrapy for this msp
        # The API uses twisted reactor which can't be restarted, better to just use cmd line
        subprocess.call(['scrapy','crawl','votes','-a','mspid='+str(msp['mspid'])],shell=True)
    mergeVotes()