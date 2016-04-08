import unittest

import mock
import irc.client

import pyborg_irc2
import pyborg

class TestConnect(unittest.TestCase):
    @mock.patch('irc.connection.socket')
    # @mock.patch('socket.socket')
    def Disabled_test_connect(self, patched_wrap, ):
        # This test is broken.
        mod = pyborg_irc2.ModIRC(pyborg.pyborg.pyborg())
        mod.start()
        # print patched_wrap.call_args
        mod.disconnect()
    
    @mock.patch('pyborg.pyborg.pyborg.learn')
    @mock.patch('irc.connection')
    def test_respond(self, c, learn):
        mod = pyborg_irc2.ModIRC(pyborg.pyborg.pyborg())
        our_event = irc.client.Event(type=None, source=None, target=None, arguments=['*', '*', 'nick'])
        mod.on_pubmsg(c, our_event)
        learn.assert_called_with(our_event.arguments[0].encode('utf-8'))
    @mock.patch('pyborg.pyborg.pyborg.reply')
    @mock.patch('pyborg.pyborg.pyborg.learn')
    @mock.patch('irc.connection')
    def test_nick_reply(self, c, learn, reply):
        mod = pyborg_irc2.ModIRC(pyborg.pyborg.pyborg())
        # nick = mod.connection.get_nickname()
        nick = 'steve'
        # c.get_nickname.return_value = "steve"
        mod.connection.real_nickname = nick
        our_event = irc.client.Event(type=None, source=None, target=None, arguments=[u'%s: yolo swagins' % nick])
        mod.on_pubmsg(c, our_event)
        learn.assert_called_with(our_event.arguments[0].split(":")[1].encode('utf-8'))
        reply.assert_called_with(u" yolo swagins")
