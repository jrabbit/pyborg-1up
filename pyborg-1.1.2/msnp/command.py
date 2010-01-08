# command.py -- Command class, and subclasses
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

import md5
import email
import email.Message
import email.Charset

from string import split, join
from binascii import hexlify, unhexlify

from codec import url_codec

class Command:
    def __init__(self, cmd = None, trn = None, args = None):
        self.cmd = cmd
        self.trn = trn
        self.args = args

    def parse(self, str):
        s = split(str)
        pos = 0
        if s == None or len(s) <= 0: return
        self.cmd, pos = s[pos], pos + 1
        if len(s) <= pos: return
        if self.cmd in ('NLN', 'FLN',
            'GTC', 'BLP', 'PRP', 'LSG', 'LST',
            'BPR'):
            self.trn = 0
        else:
            self.trn, pos = int(s[pos]), pos + 1
        if len(s) <= pos: return
        self.args, pos = tuple(s[pos:]), pos + 1

    def __str__(self):
        cmd_trn = join((self.cmd, str(self.trn)))
        if self.args != None:
            args = join(self.args)
        else:
            args = ''
        return join((cmd_trn, args))

    def send(self, conn):
        conn.send_data_line(str(self))

class Msg(Command):
    def __init__(self):
        Command.__init__(self, 'MSG')
        self.passport_id = None
        self.display_name = None
        self.msg_len = -1
        self.msg_buf = None

    def parse(self, str):
        s = split(str)
        self.cmd = s[0]
        self.passport_id = s[1]
        self.display_name = url_codec.decode(s[2])
        self.msg_len = int(s[3])

    # for fetching the message part, after the command's '\r\n'
    def receive(self, conn):
        self.msg_buf = conn.receive_data(self.msg_len)

    def send(self, conn):
        conn.send_data_line(str(self))
        conn.send_data_all(self.msg_buf)

class Png(Command):
    def __init__(self):
        self.cmd = 'PNG'
        self.trn = 0
        self.args = None

    def parse(self, str):
        pass

    def __str__(self):
        return self.cmd

class Qry(Command):  # response to server's CHL (challenge)
    def __init__(self, trn, hash):
        Command.__init__(self, 'QRY', trn, ('msmsgs@msnmsgr.com 32',))
        self.hash = hash

    def parse(self, str):
        pass

    def __str__(self):
        s = Command.__str__(self)
        m = md5.new()
        m.update(self.hash)
        m.update('Q1P7W2E4J9R8U3S5')
        digest = hexlify(m.digest())
        return s + '\n' + digest

    def send(self, conn):
        conn.send_data_all(str(self))

# vim: set ts=4 sw=4 et tw=79 :

