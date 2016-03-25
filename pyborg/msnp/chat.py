# chat.py -- Chat, ChatCallbacks classes
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

import email
import email.Message
import email.Charset

from string import split, join

from session import _Session
from command import Command, Msg
from codec import url_codec

import protocol

class ChatCallbacks:
    """Callback interface for MSN chat

    The client must implement some or all of these methods to receive
    notifications on chat events.  The value of Chat.callbacks must be set
    after receiving the Chat instance in SessionCallbacks.chat_started
    """

    def friend_joined(self, passport_id, display_name):
        """Friend has joined the chat

        Keyword arguments:
            passport_id -- string representing friend's passport ID
            display_name -- friend's display name
        """

    def friend_left(self, passport_id):
        """Friend has left the chat

        Keyword arguments:
            passport_id -- string representing friend's passport ID
        """

    def message_received(self, passport_id, display_name, text, charset):
        """Message received

        Keyword arguments:
            passport_id -- string representing friend's passport ID
            display_name -- friend's display name
            text -- message text
            charset -- character set of text (usu. utf-8)
        """

    def typing_received(self, passport_id, display_name):
        """Friend is typing

        Keyword arguments:
            passport_id -- string representing friend's passport ID
            display_name -- friend's display name
        """

class Chat(_Session):
    """MSN chat conversation

    When a conversation is started, an instance of Chat is created and passed
    on to the SessionCallbacks.chat_started method.
    """
    def __init__(self, session, server, hash, passport_id, display_name,
        session_id = None, invitee = None):

        _Session.__init__(self, ChatCallbacks())

        self.session = session
        self.hash = hash
        self.passport_id = passport_id
        self.display_name = display_name
        self.session_id = session_id
        self.transaction_id = 1
        self.initial_members = []

        self.http_proxy = session.http_proxy
        conn = self.conn = self._connect(server)

        if passport_id != session.passport_id:  # invited to chat
            ans = Command('ANS', self.transaction_id,
                (session.passport_id, hash, session_id))
            self._send_cmd(ans, conn)

            while 1:
                resp = self._receive_cmd(conn)
                if resp.cmd == 'ANS':
                    break
                elif resp.cmd != 'IRO':
                    raise Error(int(resp.cmd), protocol.errors[resp.cmd])
                self.initial_members.append((resp.args[2],
                    url_codec.decode(resp.args[3])))

        else:  # hosting chat
            usr = Command('USR', self.transaction_id,
                (passport_id, hash))
            resp = self._sync_command(usr, conn)
            if resp.cmd != 'USR':
                raise Error(int(resp.cmd), protocol.errors[resp.cmd])

            cal = Command('CAL', self.transaction_id, (invitee,))
            resp = self._sync_command(cal, conn)
            if resp.cmd != 'CAL':
                raise Error(int(resp.cmd), protocol.errors[resp.cmd])
            self.session_id = resp.args[1]

    def leave(self):
        """Leave a chat conversation

        This should be the last method called on a Chat instance.
        """
        del self.session.active_chats[self.session_id]
        self.process()
        self.conn.break_()
        self.conn = None

    def __send_mime_message(self, mime_message, flag):
        msg = Msg()
        msg.trn = self.transaction_id

        msg.msg_buf = ''
        for hdr in mime_message.items():
            msg.msg_buf = msg.msg_buf + join(hdr, ': ') + '\r\n'
        msg.msg_buf = msg.msg_buf + '\r\n'
        if mime_message.get_payload() != None:
            msg.msg_buf = msg.msg_buf + mime_message.get_payload()

        msg.args = (flag, str(len(msg.msg_buf)))

        self._async_command(msg)
        self.process()

    def send_message(self, text, charset = 'utf-8'):
        """Send message

        Keyword arguments:
            text -- message text
            charset -- character set of text (default utf-8)
        """
        mime_message = email.Message.Message()
        mime_message['MIME-Version'] = '1.0'
        mime_message['Content-Type'] = 'text/plain; charset=' + charset
        mime_message.set_payload(text)
        self.__send_mime_message(mime_message, 'N')

    def send_typing(self):
        """Send typing notification"""
        mime_message = email.Message.Message()
        mime_message['MIME-Version'] = '1.0'
        mime_message['Content-Type'] = 'text/x-msmsgscontrol'
        mime_message['TypingUser'] = self.session.passport_id
        self.__send_mime_message(mime_message, 'U')

    def process(self):
        """Process events

        This method must be called periodically, preferably in the client
        application's main loop.
        """
        while 1:
            if self.conn == None:
                break
            fd = self.conn.socket.fileno()
            r = select.select([fd], [], [], 0)
            if len(r[0]) > 0:
                buf = self.conn.receive_data_line()
                if buf == None:  # connection closed?!
                    break
                self.__process_command_buf(buf)
            elif len(self.send_queue) > 0:
                cmd = self.send_queue.pop(0)
                cmd.send(self.conn)
            else:
                break

    def __process_command_buf(self, buf):
        cmd = buf[:3]
        if cmd == 'MSG':
            self.__process_msg(buf)
        elif cmd == 'JOI':
            self.__process_joi(buf)
        elif cmd == 'BYE':
            self.__process_bye(buf)
        # TODO error handling

    def __process_msg(self, buf):
        msg = Msg()
        msg.parse(buf)
        msg.receive(self.conn)
        mime_message = email.message_from_string(msg.msg_buf)

        if mime_message.get_content_type() == 'text/plain':
            self.callbacks.message_received(msg.passport_id,
                msg.display_name,
                mime_message.get_payload(),
                mime_message.get_content_charset())

        elif mime_message.get_content_type() == 'text/x-msmsgscontrol':
            self.callbacks.typing_received(msg.passport_id,
            msg.display_name)

    def __process_joi(self, buf):
        joi = split(buf)
        self.callbacks.friend_joined(joi[1], url_codec.decode(joi[2]))

    def __process_bye(self, buf):
        bye = split(buf)
        self.callbacks.friend_left(bye[1])

# vim: set ts=4 sw=4 et tw=79 :

