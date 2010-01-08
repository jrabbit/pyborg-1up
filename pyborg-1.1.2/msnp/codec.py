# codec.py -- UrlCodec class, url_codec global
#
# Copyright (C) 2003 Manish Jethani (manish_jethani AT yahoo.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from string import split, join
from binascii import hexlify, unhexlify

class UrlCodec:  # url-encoding (rfc 1738)
    def encode(self, str):
        if str == None:
            return None
        buf = []
        for c in str:
            h = hexlify(c)
            i = ord(c)
            if 0x00 <= i <= 0x20 or i == 0x7f or 0x80 <= i <= 0xff:
                buf.append('%')
                buf.append(h)
            else:
                buf.append(c)
        return join(buf, '')

    def decode(self, str):
        if str == None:
            return None
        buf = []
        p = hex = None
        for c in str:
            if c == '%':
                p = '%'
            elif p != None:
                (hex, p) = (c, None)
            elif hex != None:
                hex = hex + c
                buf.append(unhexlify(hex))
                hex = None
            else:
                buf.append(c)
        return join(buf, '')
url_codec = UrlCodec()

# vim: set ts=4 sw=4 et tw=79 :

