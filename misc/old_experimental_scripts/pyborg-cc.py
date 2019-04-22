import string
import sys
import pyborg
import os

class ccpyborg:
    def __init__(self, my_pyborg, my_msg):
        self.pyborg=my_pyborg
        self.pyborg.process_msg(self, my_msg, 100, 1, ( None ), owner = 1)
    def output(self, message, args):
        ccua='pyborg'
        ccremote='http://moules.org/?q=board/backend'
        ccadd='http://moules.org/?q=board/add'
        messageout=''
        mystring='curl -A '+ccua+' -k -e '+ccremote+' -d "message='+message+'" -d "section=1" '+ccadd
        print mystring
        os.system(mystring)
        print message


if __name__ == "__main__":
    my_pyborg = pyborg.pyborg()
    my_msg=sys.argv[1]
    print "pyplop"
    ccpyborg(my_pyborg, my_msg)
    print "2"
    my_pyborg.save_all()
    print "3"
    del my_pyborg
    print "4"
