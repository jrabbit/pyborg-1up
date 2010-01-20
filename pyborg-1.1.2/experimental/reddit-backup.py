#!/usr/bin/env python
"""
Reddit backup!
Version: 10.01.11
"""
import codecs
import re
import time
import urllib
import urllib2
from xml.dom import minidom

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        print "Unable to find a json library. Please install simplejson or Python 2.6.* if you want to backup as json."
        exit()
        

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor)
def urlopen(url, data=None, headers = {}): 
    if hasattr(data, "__iter__"):
        data = urllib.urlencode(data)
    return opener.open(urllib2.Request(url, data, headers))

if __name__ == "__main__":
    HASBACON = False
    format = None
    datetime = time.strftime("%Y%m%d%H%M%S", time.gmtime())

    while not HASBACON:
        username = raw_input("Username: ")
        password = raw_input("Password: ")
        if "WRONG_PASSWORD" in urlopen("https://www.reddit.com/api/login/", {"passwd": password, "user": username}).read():
            print "Wrong username or password, please try again."
        else:
            HASBACON = True
    
    while not format:
        f = raw_input("Save backup as (x)ml or (j)son? ")
        if f.lower().startswith("x"):
            format = "xml"
        elif f.lower().startswith("j"):
            format = "json"
        else:
            print "No such option, please try again."
    
    for section in ["comments", "submitted", "liked", "disliked", "hidden"]:
        print "Downloading %s..." % section
        after = ""
        data = []
        xml = None
        count = 0
        while not after is None:
            c = json.loads(urlopen("http://www.reddit.com/user/%s/%s/.json?after=%s" % (urllib.quote(username), section, after)).read())
            if format == "xml":
                x = minidom.parseString(urlopen("http://www.reddit.com/user/%s/%s/.xml?after=%s" % (urllib.quote(username), section, after)).read())
                if not xml:
                    xml = x
                else:
                    for item in x.getElementsByTagName("item"):
                        xml.childNodes[0].childNodes[0].appendChild(item)

            else:
                data.extend(c["data"]["children"])
            after = c["data"]["after"]
            count += len(c["data"]["children"])
            
        f = codecs.open("reddit.%s.%s.%s" % (section, datetime, format), "w", "utf-8")
        
        if format == "json":
            json.dump(data, f, sort_keys=True, indent=4, encoding="utf-8")
        else:
            xml.writexml(f, encoding="utf-8")
            
        f.close()
        print "Saved %d %s." % (count, section)
    
    print "Mission Accomplished."