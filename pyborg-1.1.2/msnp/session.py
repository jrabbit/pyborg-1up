# session.py -- Session, SessionCallbacks classes
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

import select
import md5

from string import split, join
from binascii import hexlify, unhexlify
from time import time

from protocol import States, Lists, PrivacyModes
from error import Error, HttpError
from friend import Group, Friend, FriendList
from net import Connection, HttpProxyConnection
from command import Command, Msg, Png, Qry
from codec import url_codec

import protocol
import chat

class _Session:  # common base for Session and Chat
    def __init__(self, callbacks):
        self.callbacks = callbacks
        self.transaction_id = 0
        self.http_proxy = None
        self.conn = None
        self.send_queue = []

    def _connect(self, server):
        conn = None
        if self.http_proxy:
            conn = HttpProxyConnection(server, self.http_proxy)
        else:
            conn = Connection(server)
        conn.establish()
        return conn

    def _increment_transaction_id(self):
        self.transaction_id = self.transaction_id + 1
        return self.transaction_id

    def _send_cmd(self, cmd, conn):
        conn.send_data_line(str(cmd))
        self._increment_transaction_id()

    def _receive_cmd(self, conn):
        buf = conn.receive_data_line()
        if buf == None:  # connection closed
            raise Error(1, 'Connection closed.')
        cmd = Command()
        cmd.parse(buf)
        return cmd

    def _sync_command(self, cmd, conn):
        # synchronous command (receive response immediately)
        self._send_cmd(cmd, conn)
        return self._receive_cmd(conn)

    def _async_command(self, cmd):
        self.send_queue.append(cmd)
        self._increment_transaction_id()

class SessionCallbacks:  # callback interface
    """Callback interface for MSN instant messaging session

    To receive notification on various protocol events, the client must
    implement some or all of the methods in this callback interface.
    """

    def ping(self):
        """Ping received from server"""

    def state_changed(self, state):
        """User's presence state has changed

        Keyword arguments:
            state -- any of the msnp.States members
        """

    def friend_online(self, state, passport_id, display_name):
        """Friend is online

        Keyword arguments:
            state -- any of the msnp.States members
            passport_id -- string representing friend's passport ID
            display_name -- friend's display name
        """

    def friend_offline(self, passport_id):
        """Friend is offline

        Keyword arguments:
            passport_id -- string representing friend's passport ID
        """

    def friend_list_updated(self, friend_list):
        """Friend list has been updated

        Keyword arguments:
            friend_list -- same as msnp.Session.friend_list
        """

    def logged_out(self):
        """User has been logged out"""

    def group_added(self, id, name):
        """Group has been added

        Keyword arguments:
            id -- group ID
            name -- name of group
        """

    def group_removed(self, id):
        """Group has been removed

        Keyword arguments:
            id -- group ID
        """

    def group_renamed(self, id, name):
        """Group has been renamed

        Keyword arguments:
            id -- group ID
            name -- new name of group
        """

    def friend_added(self, list_, passport_id, display_name, group_id = -1):
        """Friend has been added

        If list_ is msnp.Lists.REVERSE, it means that the user has been added
        to someone's list.  In that case, the passport_id and display_name
        parameters contain information about that someone.

        Keyword arguments:
            list_ -- type of list (allow, block, etc.)
            passport_id -- string representing friend's passport ID
            display_name -- friend's display name
            group_id -- group ID of group to which friend has been added
        """

    def friend_removed(self, list_, passport_id, group_id = -1):
        """Friend has been removed

        Keyword arguments:
            list_ -- type of list (allow, block, etc.)
            passport_id -- string representing friend's passport ID
            group_id -- group ID of group from which friend has been removed
        """

    def display_name_changed(self, display_name):
        """Display name changed

        Keyword arguments:
            display_name -- user's new display name
        """

    def display_name_received(self, passport_id, display_name):
        """Display name received

        Keyword arguments:
            passport_id -- string representing friend's passport ID
            display_name -- friend's display name
        """

    def chat_started(self, chat):
        """Chat started

        Keyword arguments:
            chat -- Chat instance representing new chat started
        """

class Session(_Session):
    """MSN instant messaging session

    To get into an instant messaging session, an instance of msnp.Session must
    be created.  The session can be started by calling the login method.  After
    logging in, the process method must be called periodically to process the
    server's commands.
    """

    class __ChatRequest:
        def __init__(self, invitee):
            self.invitee = invitee

    def __init__(self, callbacks = None, dispatch_server = None):
        """Constructor for msnp.Session

        Keyword arguments:
            callbacks -- callback interface
            dispatch_server -- dispatch server host, port
        """

        if callbacks == None:
            callbacks = SessionCallbacks()
        _Session.__init__(self, callbacks)

        if dispatch_server == None:
            self.dispatch_server = ('messenger.hotmail.com', 1863)

        self.logged_in = 0
        self.passport_id = None
        self.display_name = None
        self.chat_requests = {}
        self.friend_list = FriendList()
        self.active_chats = {}

    def __get_twn_ticket(self, twn_string, username, password):
        from net import HTTPSConnection
        from urllib import urlencode
        debuglevel = 0

        # step 1: get address of login server
        con = HTTPSConnection('nexus.passport.com',
            http_proxy = self.http_proxy)
        con.set_debuglevel(debuglevel)
        con.request('GET', '/rdr/pprdr.asp')
        res = con.getresponse()
        con.close()
        if res.status != 200:
            raise HttpError(0, 'Bad response from passport nexus server.',
                res.status, res.reason)
        hdr = res.getheader('PassportURLs')
        url = {}
        for u in hdr.split(','):
            k, v = u.split('=')
            url[k] = v
        dalogin = url['DALogin'].split('/', 1)

        # step 2: get "ticket" to notification server
        while True:
            con = HTTPSConnection(dalogin[0], http_proxy = self.http_proxy)
            con.set_debuglevel(debuglevel)
            auth = 'Passport1.4 OrgVerb=GET,%s,%s,%s,%s' \
                % (urlencode({'OrgURL': 'http://messenger.msn.com'}),
                    urlencode({'sign-in': username}),
                    urlencode({'pwd': password}),
                    twn_string)
            con.request('GET', '/%s' % (dalogin[1]), '',
                {'Authorization': auth})
            res = con.getresponse()
            con.close()
            if res.status != 200:
                raise HttpError(0, 'Bad response from login server.',
                    res.status, res.reason) # XXX handle redirection?
            else:
                break
        hdr = res.getheader('Authentication-Info') or \
              res.getheader('WWW-Authenticate')
        hdr = hdr[len('Passport1.4 '):]
        auth = {}
        for u in hdr.split(','):
            k, v = u.split('=', 1)
            if v[0] == '\'' and v[-1] == '\'':
                v = v[1:-1]
            auth[k] = v
        ticket = auth['from-PP']

        return ticket
        # TODO code cleanup

    def __handshake(self, server, username, password):
        conn = self._connect(server)
        try:
            ver = Command('VER', self.transaction_id, ('MSNP8', 'CVR0'))
            resp = self._sync_command(ver, conn)
            if resp.cmd != 'VER' or resp.args[0] == '0':
                raise Error(0, 'Bad response for VER command.')

            cvr = Command('CVR', self.transaction_id,
                ('0x0409', 'win', '4.10', 'i386', 'MSNMSGR', '6.0.0602',
                'MSMSGS ', username))
            resp = self._sync_command(cvr, conn)
            if resp.cmd != 'CVR':
                raise Error(0, 'Bad response for CVR command.')

            usr = Command('USR', self.transaction_id, ('TWN', 'I', username))
            resp = self._sync_command(usr, conn)
            if resp.cmd != 'USR' and resp.cmd != 'XFR':
                raise Error(0, 'Bad response for USR command.')

            # for dispatch server, response is ver, cvr, xfr; for notification
            # server, it is ver, cvr, usr (or same as dispatch server, in some
            # cases)

            if resp.cmd == 'XFR':
                return split(resp.args[1], ':', 1)
            elif resp.cmd == 'USR':
                twn_string = resp.args[2]

                ticket = self.__get_twn_ticket(twn_string, username, password)

                usr = Command('USR', self.transaction_id, ('TWN', 'S', ticket))
                resp = self._sync_command(usr, conn)
                if resp.cmd != 'USR':
                    raise Error(int(resp.cmd), protocol.errors[resp.cmd])
                elif resp.args[0] != 'OK':
                    raise Error(0, 'Bad response for USR command.')

                self.passport_id = resp.args[1]
                self.display_name = url_codec.decode(resp.args[2])
                self.logged_in = 1
        finally:
            if not self.logged_in:
                conn.break_()
            else:
                self.conn = conn

    def process(self, chats = False):
        """Process events

        Keyword arguments:
            chats -- whether or not to call msnp.Chat.process for all active
                chat sessions

        This method must be called periodically, preferably in the client
        application's main loop.
        """
        while self.logged_in:
            fd = self.conn.socket.fileno()
            r = select.select([fd], [], [], 0)
            if len(r[0]) > 0:
                buf = self.conn.receive_data_line()
                self.__process_command_buf(buf)
            elif len(self.send_queue) > 0:
                cmd = self.send_queue.pop(0)
                cmd.send(self.conn)
            else:
                break
        if chats:
            self.__process_active_chats()

    def __process_active_chats(self):
        [chat_.process() for chat_ in self.active_chats.values()]

    def __process_command_buf(self, buf):
        cmd = buf[:3]
        if cmd == 'MSG':
            self.__process_msg(buf)
        elif cmd == 'QNG':
            self.__process_qng(buf)
        elif cmd == 'OUT':
            self.__process_out(buf)
        elif cmd == 'RNG':
            self.__process_rng(buf)
        else:
            c = Command()
            c.parse(buf)
            if c.cmd == 'CHG':
                self.__process_chg(c)
            elif c.cmd == 'ILN':
                self.__process_iln(c)
            elif c.cmd == 'NLN':
                self.__process_nln(c)
            elif c.cmd == 'FLN':
                self.__process_fln(c)
            elif c.cmd == 'CHL':
                self.__process_chl(c)
            elif c.cmd == 'LSG':
                self.__process_lsg(c)
            elif c.cmd == 'LST':
                self.__process_lst(c)
            elif c.cmd == 'SYN':
                self.__process_syn(c)
            elif c.cmd == 'XFR':
                self.__process_xfr(c)
            elif c.cmd == 'BLP':
                self.__process_blp(c)
            elif c.cmd == 'GTC':
                self.__process_gtc(c)
            elif c.cmd == 'ADG':
                self.__process_adg(c)
            elif c.cmd == 'RMG':
                self.__process_rmg(c)
            elif c.cmd == 'REG':
                self.__process_reg(c)
            elif c.cmd == 'ADD':
                self.__process_add(c)
            elif c.cmd == 'REM':
                self.__process_rem(c)
            elif c.cmd == 'REA':
                self.__process_rea(c)
            elif c.cmd == '218':
                pass
            # TODO error handling

    def __process_msg(self, buf):
        msg = Msg()
        msg.parse(buf)
        msg.receive(self.conn)
        # discard NS messages for now

    def __process_qng(self, buf):
        self.callbacks.ping()

    def __process_out(self, buf):
        self.conn.break_()
        self.conn = None
        self.logged_in = 0
        self.callbacks.logged_out()

    def __process_rng(self, buf):
        cmdline = split(buf)
        session_id = cmdline[1]
        sb = split(cmdline[2], ':')
        server = (sb[0], int(sb[1]))
        hash = cmdline[4]
        passport_id = cmdline[5]
        display_name = url_codec.decode(cmdline[6])
        try:
            chat_ = chat.Chat(self, server, hash, passport_id,
                display_name, session_id)
        except Error, e:
            if e.code == 1:  # connection closed
                return
            raise e
        self.active_chats[chat_.session_id] = chat_
        self.callbacks.chat_started(chat_)

    def __process_chg(self, command):
        self.callbacks.state_changed(command.args[0])

    def __process_iln(self, command):
        state = command.args[0]
        passport_id = command.args[1]
        display_name = url_codec.decode(command.args[2])
        friend = self.friend_list.get_friend(passport_id)
        if friend != None:
            friend.state = state
            friend.display_name = display_name
            self.__friend_list_updated()
        else:  # usu. immed. after login
            self.friend_list.temp_iln[passport_id] = state
        self.callbacks.friend_online(state, passport_id, display_name)

    def __process_nln(self, command):
        state = command.args[0]
        passport_id = command.args[1]
        display_name = url_codec.decode(command.args[2])
        friend = self.friend_list.get_friend(passport_id)
        if friend != None:
            friend.display_name = display_name
            friend.state = state
            self.__friend_list_updated()
        self.callbacks.friend_online(state, passport_id, display_name)

    def __process_fln(self, command):
        passport_id = command.args[0]
        friend = self.friend_list.get_friend(passport_id)
        if friend != None:
            friend.state = States.OFFLINE
            self.__friend_list_updated()
        self.callbacks.friend_offline(passport_id)

    def __process_chl(self, command):
        qry = Qry(self.transaction_id, command.args[0])
        self._async_command(qry)

    def __process_lsg(self, command):
        id = int(command.args[0])
        name = url_codec.decode(command.args[1])

        group = Group(id, name)
        self.friend_list.groups[id] = group

        self.__friend_list_updated()

    def __process_lst(self, command):
        from protocol import list_flags

        passport_id  = command.args[0]
        display_name = url_codec.decode(command.args[1])
        list_        = int(command.args[2])
        group_id     = []

        if list_ & list_flags[Lists.FORWARD]:
            group_id = [int(i) for i in split(command.args[3], ',')]

        groups = None
        if len(group_id):
            groups = [self.friend_list.groups[g_id] for g_id in group_id]

        friend = Friend(passport_id, display_name, groups = groups)
        for f in list_flags.keys():
            if list_ & list_flags[f]:
                self.friend_list.lists[f][passport_id] = friend

        if self.friend_list.temp_iln.has_key(passport_id):
            friend.state = self.friend_list.temp_iln[passport_id]

        self.__friend_list_updated()

    def __process_syn(self, command):
        ver = int(command.args[0])
        self.friend_list.ver = ver
        self.__friend_list_updated()

    def __process_xfr(self, command):
        sb = split(command.args[1], ':')
        server = (sb[0], int(sb[1]))
        cr = self.chat_requests[command.trn]
        invitee = cr.invitee
        chat_ = chat.Chat(self, server, command.args[3], self.passport_id,
            self.display_name, None, invitee)
        self.active_chats[chat_.session_id] = chat_
        self.callbacks.chat_started(chat_)

    def __process_blp(self, command):
        privacy_mode = command.args[0]
        self.friend_list.privacy_mode = privacy_mode
        self.__friend_list_updated()

    def __process_gtc(self, command):
        notify_on_add = command.args[0] == 'A'
        self.friend_list.notify_on_add_ = notify_on_add
        self.__friend_list_updated()

    def __process_adg(self, command):
        ver = int(command.args[0])
        name = url_codec.decode(command.args[1])
        id = int(command.args[2])
        self.friend_list.ver = ver
        self.friend_list.groups[id] = Group(id, name)
        self.__friend_list_updated()
        self.callbacks.group_added(id, name)

    def __process_rmg(self, command):
        ver = int(command.args[0])
        id = int(command.args[1])
        self.friend_list.ver = ver
        if self.friend_list.groups.has_key(id):
            del self.friend_list.groups[id]
        self.__friend_list_updated()
        self.callbacks.group_removed(id)

    def __process_reg(self, command):
        ver = int(command.args[0])
        id = int(command.args[1])
        name = url_codec.decode(command.args[2])
        self.friend_list.ver = ver
        if self.friend_list.groups.has_key(id):
            self.friend_list.groups[id].name = name
        self.__friend_list_updated()
        self.callbacks.group_renamed(id, name)

    def __process_add(self, command):
        list_ = command.args[0]
        ver = int(command.args[1])
        passport_id = command.args[2]
        display_name = url_codec.decode(command.args[3])
        group = None
        if list_ == Lists.FORWARD:
            group = self.friend_list.groups[int(command.args[4])]

        self.friend_list.ver = ver
 
        friend = self.friend_list.get_friend(passport_id, list_)
        if friend != None:
            friend.add_to_group(group)
        else:
            if group != None:
                friend = Friend(passport_id, passport_id, (group))
            else:
                friend = Friend(passport_id, passport_id)
            self.friend_list.lists[list_][passport_id] = friend

        self.__friend_list_updated()

        if group != None:
            self.callbacks.friend_added(list_, passport_id, display_name,
                group.get_id())
        else:
            self.callbacks.friend_added(list_, passport_id, display_name)

    def __process_rem(self, command):
        list_ = command.args[0]
        ver = int(command.args[1])
        passport_id = command.args[2]
        group = None
        if list_ == Lists.FORWARD:
            group = self.friend_list.groups[int(command.args[3])]

        self.friend_list.ver = ver

        friend = self.friend_list.get_friend(passport_id, list_)
        if friend != None: # this shouldn't be None, unless friend_list stale
            if group != None:
                friend.remove_from_group(group)
            if len(friend.get_groups()) == 0:
                del self.friend_list.lists[list_][passport_id]

        self.__friend_list_updated()
        if group != None:
            self.callbacks.friend_removed(list_, passport_id, group.get_id())
        else:
            self.callbacks.friend_removed(list_, passport_id)

    def __process_rea(self, command):
        ver = int(command.args[0])
        passport_id = command.args[1]
        display_name = url_codec.decode(command.args[2])

        if passport_id == self.passport_id:
            self.display_name = display_name
            self.callbacks.display_name_changed(display_name)
        else:
            self.callbacks.display_name_received(passport_id, display_name)

    def __friend_list_updated(self):
        self.friend_list.updated = time()
        self.callbacks.friend_list_updated(self.friend_list)

    def login(self, username, password, initial_state = States.ONLINE):
        """Login to MSN server

        Keyword arguments:
            username -- username
            password -- password
            initial_state -- initial state (default msnp.States.ONLINE)
        """
        if self.logged_in:
            return
        server = self.dispatch_server
        while not self.logged_in:
            server = self.__handshake(server, username, password)
        self.change_state(initial_state)

    def ping(self):
        """Ping server"""
        if not self.logged_in:
            return
        self._async_command(Png())
        self.process()

    def logout(self):
        """Logout from server"""
        if not self.logged_in:
            return
        [chat_.leave() for chat_ in self.active_chats.values()]
        self.process()
        self.conn.break_()
        self.conn = None
        self.logged_in = 0

    def change_state(self, state):
        """Change user's state

        Keyword arguments:
            state -- new state (see msnp.States)
        """
        if not self.logged_in:
            return
        chg = Command('CHG', self.transaction_id, (state,))
        self._async_command(chg)
        self.process()

    def sync_friend_list(self, ver = -1):
        """Synchronise friend list by getting new copy from server

        The friend list is updated asynchronously.
        msnp.SessionCallbacks.friend_list_updated will be called repeatedly
        after a call to this method.  The client may want to set a timer
        instead, and check for updates to the friend list using the
        msnp.FriendList.last_updated method.

        Keyword arguments:
            ver -- friend list version
        """
        if not self.logged_in:
            return
        self.friend_list.dirty = False
        if ver == -1:
            ver = self.friend_list.ver
        syn = Command('SYN', self.transaction_id, (str(ver),))
        self._async_command(syn)
        self.process()

    def request_list(self, list_ = Lists.FORWARD):
        """Request a list from the server

        Keyword arguments:
            list_ -- type of list to request (see msnp.Lists)
        """
        if not self.logged_in:
            return
        lst = Command('LST', self.transaction_id, (list_,))
        self._async_command(lst)
        self.process()

    def request_groups(self):
        """Request groups from server"""
        if not self.logged_in:
            return
        lsg = Command('LSG', self.transaction_id, ())
        self._async_command(lsg)
        self.process()

    def change_privacy_mode(self, privacy_mode):
        """Change privacy mode

        Keyword arguments:
            privacy_mode -- new privacy mode (see msnp.PrivacyModes)
        """
        if not self.logged_in:
            return
        blp = Command('BLP', self.transaction_id, (privacy_mode,))
        self._async_command(blp)
        self.process()

    def notify_on_add(self, notify):
        """Change setting for being notified on being added"""
        if not self.logged_in:
            return
        setting = 'N'
        if notify:
            setting = 'A'
        gtc = Command('GTC', self.transaction_id, (setting,))
        self._async_command(gtc)
        self.process()

    def add_group(self, name):
        """Add a group
        
        Keyword arguments:
            name -- name of new group
        """
        if not self.logged_in:
            return
        adg = Command('ADG', self.transaction_id,
            (url_codec.encode(name), '0'))
        self._async_command(adg)
        self.process()

    def remove_group(self, id):
        """Remove a group

        Keyword arguments:
            id -- group ID
        """
        if not self.logged_in:
            return
        rmg = Command('RMG', self.transaction_id, (str(id),))
        self._async_command(rmg)
        self.process()

    def rename_group(self, id, name):
        """Rename a group

        Keyword arguments:
            id -- group ID
            name -- new name of group
        """
        if not self.logged_in:
            return
        reg = Command('REG', self.transaction_id,
            (str(id), url_codec.encode(name), '0'))
        self._async_command(reg)
        self.process()

    def add_friend(self, list_, passport_id, group_id = 0):
        """Add a friend

        Keyword arguments:
            list_ -- type of list (allow, block, etc.)
            passport_id -- string representing friend's passport ID
            group_id -- group ID of group to which friend is being added
        """
        add = None
        if list_ == Lists.FORWARD:
            add = Command('ADD', self.transaction_id,
                (list_, passport_id, passport_id, str(group_id)))
        else:
            add = Command('ADD', self.transaction_id,
                (list_, passport_id, passport_id))
        self._async_command(add)
        self.process()

    def remove_friend(self, list_, passport_id, group_id = 0):
        """Remove a friend

        Keyword arguments:
            list_ -- type of list (allow, block, etc.)
            passport_id -- string representing friend's passport ID
            group_id -- group ID of group from which friend is being removed
        """
        rem = None
        if list_ == Lists.FORWARD:
            rem = Command('REM', self.transaction_id,
                (list_, passport_id, str(group_id)))
        else:
            rem = Command('REM', self.transaction_id,
                (list_, passport_id))
        self._async_command(rem)
        self.process()

    def change_display_name(self, display_name):
        """Change user's display name

        Keyword arguments:
            display_name -- user's new display name
        """
        if not self.logged_in:
            return
        rea = Command('REA', self.transaction_id,
            (self.passport_id, url_codec.encode(display_name)))
        self._async_command(rea)
        self.process()

    def request_display_name(self, passport_id):
        """Request display name of a friend

        Keyword arguments:
            passport_id -- string representing friend's passport ID
        """
        if not self.logged_in:
            return
        rea = Command('REA', self.transaction_id,
            (passport_id, url_codec.encode('MJ++')))
        self._async_command(rea)
        self.process()

    def start_chat(self, invitee):
        """Start a chat

        Keyword arguments:
            invitee -- friend invited for chat
        """
        if not self.logged_in:
            return
        xfr = Command('XFR', self.transaction_id, ('SB',))
        self._async_command(xfr)
        self.chat_requests[xfr.trn] = Session.__ChatRequest(invitee)
        self.process()

# vim: set ts=4 sw=4 et tw=79 :

