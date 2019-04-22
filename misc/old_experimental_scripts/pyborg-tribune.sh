#!/bin/sh
LASTMESSAGE="$(curl -s -k -A wmCoinCoin http://moules.org/?q=board/backend | awk -f cc.awk | sed -e 's/<message>//g'| sed -e 's/pyborg\&lt;//g' | sed -e 's/\&lt;//g'| tail -2 |cut -f 3- -d \ )"
LASTLOGIN="$(echo $LASTMESSAGE|awk '{print $2}')"
echo $LASTMESSAGE
./pyborgcc.py "$LASTMESSAGE
