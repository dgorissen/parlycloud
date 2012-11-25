from bs4 import BeautifulSoup
import urllib
import re
import json
import glob
import os

def get_topics_yahoo(text):
    url = 'http://search.yahooapis.com/ContentAnalysisService/V1/termExtraction'
    appid = 'YahooDemo'

    params = urllib.urlencode({
        'appid': appid,
        'context': text,
        'output': "json"
    })
    rawdata = urllib.urlopen(url, params).read()
    output = json.loads(rawdata)

    return output['ResultSet']['Result']

def get_topics_zemanta(text):
    api_key = "zwkxnmyvxvlz2vqmlzwnggkk"
    gateway = 'http://api.zemanta.com/services/rest/0.0/'
    args = {'method': 'zemanta.suggest',
                    'api_key': api_key,
                    'text': text,
                    'return_categories': 'dmoz',
                    'return_images':'Yes',
                    'images_limit':10,
                    'format': 'json'}

    args_enc = urllib.urlencode(args)
    raw_output = urllib.urlopen(gateway, args_enc).read()
    output = json.loads(raw_output)
    
    kwds = output['keywords']
    cats = output['categories']
    imgs = [x["url_m"] for x in output['images']]
    
    return kwds,cats,imgs

def get_files():
    for f in  sorted(glob.glob('xml/*.xml')):
        yield f

def load_cache():
    fn = "cache.json"
    if os.path.exists(fn):
        resfile = open(fn,"r")
        results = json.load(resfile)
        resfile.close()
        return results
    else:
        return {}

def save_cache(data):
        fn = "cache.json"
        resfile = open(fn,"w")
        json.dump(data,resfile)
        resfile.close()

def build_cache():

    results = load_cache()

    for fname in get_files():
        if fname in results: 
            print "Already have ", fname, "skipping"
            continue

        print "\n*******", fname
        rawdata = str(open(fname).read())
        b = BeautifulSoup(rawdata,"lxml")

        txt = b.get_text()
        txt = txt.encode('ascii','ignore')
        txt = re.sub('[^\w\.,: ]','',txt)
        kwds,cats,imgs = get_topics_zemanta(txt)
        
        print 
        print kwds

        fn = os.path.basename(fname).replace("debates","").replace(".xml","")
        results[fn] = {"topics":kwds,"categories":cats,"images":imgs}

        save_cache(results)

def main():
    from flask import Flask, render_template
    app = Flask(__name__)
    
    data = load_cache()
    dates = sorted(data.keys())

    @app.route('/')
    @app.route('/<path:date>')
    def main_view(date=None):
        print "date is ",date
        
        if date == "favicon.ico": return ""

        if not date:
            curdate = dates[0]
            next = dates[1]
            prev = dates[0]
        else:
            curdate = date
            i = dates.index(curdate)
            next = dates[min(i+1,len(dates)-1)]
            prev = dates[max(i-1,0)]
        
        # prepare category url
        d = data[curdate]
        cats = d["categories"]
        for c in cats:
            c["name"] = c["name"].replace("Top/","")
            c["shortname"] = "/".join(c["name"].split("/")[-2:])
        d["categories"] = cats
        
        return  render_template("main.html",data=d,next=next,prev=prev,date=curdate)

    app.run(debug=True)

if  __name__ == "__main__":
    #build_cache()
    main()
