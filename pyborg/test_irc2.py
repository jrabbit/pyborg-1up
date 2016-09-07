import unittest

try:
    from unittest import mock
except ImportError:
    import mock
import irc.client

import pyborg_irc2
import pyborg


class TestReplys(unittest.TestCase):
    # @mock.patch('socket.socket.connect')
    # # @mock.patch('socket.socket')
    # def test_connect(self, patched_wrap, ):
    #     # This test is doesn't test anything and starts a loop
    #     mod = pyborg_irc2.ModIRC(pyborg.pyborg.pyborg)
    #     mod.start()
    #     print patched_wrap.call_args
    #     mod.disconnect()
    settings = {'multiplex': True,
                'nickname': 'PyBorg',
                'password': '',
                'quitmsg': 'Bye :-(',
                'realname': 'Pyborg',
                'reply2ignored': False,
                'server': {'channels': [{'chan': '#ranarchism',
                                         'reply_chance': 5,
                                         'speaking': True},
                                        {'chan': '#queertoo', 'reply_chance': 5, 'speaking': False}],
                           'ignorelist': [],
                           'owners': ['jrabbit'],
                           'port': 6697,
                           'server': 'chat.freenode.net',
                           'ssl': True},
                'speaking': True,
                'speakingchans': ['#test'],
                'stealth': False}

    @mock.patch('pyborg_irc2.ModIRC.strip_nicks', side_effect=lambda x, _: x)
    @mock.patch('pyborg_irc2.ModIRC.learn')
    @mock.patch('irc.connection')
    def test_respond(self, c, learn, stripnicks):
        mod = pyborg_irc2.ModIRC(pyborg.pyborg.pyborg, self.settings)
        our_event = irc.client.Event(
            type=None, source=None, target=u"#ranarchism", arguments=[u"Hello Pyborg"])
        mod.on_pubmsg(c, our_event)
        learn.assert_called_with(our_event.arguments[0].encode('utf-8'))

    @mock.patch('pyborg_irc2.ModIRC.strip_nicks', side_effect=lambda x, _: x)
    @mock.patch('pyborg_irc2.ModIRC.reply')
    @mock.patch('pyborg_irc2.ModIRC.learn')
    @mock.patch('irc.connection')
    def test_nick_reply(self, c, learn, reply, stripnicks):
        mod = pyborg_irc2.ModIRC(pyborg.pyborg.pyborg, self.settings)
        # nick = mod.connection.get_nickname()
        nick = 'steve'
        # c.get_nickname.return_value = "steve"
        mod.connection.real_nickname = nick
        our_event = irc.client.Event(
            type=None, source=None, target=None, arguments=[u'%s: yolo swagins' % nick])
        mod.on_pubmsg(c, our_event)
        learn.assert_called_with(
            our_event.arguments[0].split(":")[1].encode('utf-8'))
        reply.assert_called_with(b" yolo swagins")

    @mock.patch('random.choice')
    def test_nick_replace(self, patched_choice):
        mod = pyborg_irc2.ModIRC(pyborg.pyborg.pyborg, self.settings)
        our_event = irc.client.Event(type=None, source=None, target="#botally")
        mocked_channel = mock.Mock()
        patched_choice.return_value = "jrabbit"
        mod.channels = {"#botally": mocked_channel}
        msg = "#nick is the best bot maker!"
        output = mod.replace_nicks(msg, our_event)
        mocked_channel.users.assert_called_with()
        self.assertEqual(output, "jrabbit is the best bot maker!")

    def test_nick_strip(self):
        mod = pyborg_irc2.ModIRC(pyborg.pyborg.pyborg, self.settings)
        our_event = irc.client.Event(type=None, source=None, target="#botally")
        mocked_channel = mock.Mock()
        mocked_channel.users.return_value = ["jrabbit"]
        mod.channels = {"#botally": mocked_channel}
        msg = "jrabbit is the best bot maker!"
        self.assertEqual(mod.strip_nicks(msg, our_event), "#nick is the best bot maker!")

