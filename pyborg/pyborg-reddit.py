#!/usr/bin/env python
#
# PyBorg reddit file input module
#
# Copyright (c) 2000, 2006, 2010 Tom Morton, Sebastien Dailly, Jrabbit
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#        
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
import string
import sys
from urllib2 import urlopen
import simplejson as json
import time
from pyborg import pyborg

class ModRedditIn:
    """
    Module for reddit input. Learning from reddit, is that even possible?
    """

    # Command list for this module
    commandlist = "Reddit Module Commands:\nNone"
    commanddict = {}
    
    def __init__(self, Borg):
        #begin copypasta thanks http://github.com/ketralnis/redditron/blob/master/redditron.py
        url = 'http://www.reddit.com/comments.json?limit=100'
        while True:
            s = urlopen(url).read().decode('utf8')

            js = json.loads(s)
            cms = js['data']['children']
            bodies = {}

            
            for cm in cms:
                cm = cm['data']
                print type(cms), type(cm)
                if cm.get('body', None):
                    bodies[cm['id']] = cm['body']
            #end copypasta
            print "I knew "+`Borg.settings.num_words`+" words ("+`len(Borg.lines)`+" lines) before reading Reddit.com"
        #   cm['body'] = buffer
            for k in bodies:
                #print cm['id'], k
                buffer = pyborg.filter_message(bodies[cm['id']], Borg)
            # Learn from input
                try:
                    print buffer
                    Borg.learn(buffer)
                except KeyboardInterrupt, e:
                # Close database cleanly
                    print "Premature termination :-("
            print "I know "+`Borg.settings.num_words`+" words ("+`len(Borg.lines)`+" lines) now."

    def shutdown(self):
        pass

    def start(self):
        sys.exit()

    def output(self, message, args):
        pass

if __name__ == "__main__":
    # if len(sys.argv) < 2:
    #   print "Specify a filename."
    #   sys.exit()
    # start the pyborg
    # No need for this, we don't have any args to process (until I add subredits)
    my_pyborg = pyborg.pyborg()
    ModRedditIn(my_pyborg)
    my_pyborg.save_all()
    del my_pyborg

