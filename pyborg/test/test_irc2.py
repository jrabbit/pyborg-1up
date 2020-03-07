import unittest
from unittest import mock

import irc.client

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
    settings = {
        "multiplex": True,
        "nickname": "PyBorg",
        "password": "",
        "quitmsg": "Bye :-(",
        "realname": "Pyborg",
        "reply2ignored": False,
        "server": {
            "channels": [
                {"chan": "#ranarchism", "reply_chance": 5, "speaking": True},
                {"chan": "#queertoo", "reply_chance": 5, "speaking": False},
            ],
            "owners": ["jrabbit"],
            "port": 6697,
            "server": "chat.freenode.net",
            "ssl": True,
            "ignorelist": ["title"],
        },
        "speaking": True,
        "speakingchans": ["#test"],
        "stealth": False,
    }

    @mock.patch("pyborg.mod.mod_irc.ModIRC.strip_nicks", side_effect=lambda x, _: x)
    @mock.patch("pyborg.mod.mod_irc.ModIRC.reply")
    @mock.patch("pyborg.mod.mod_irc.ModIRC.learn")
    @mock.patch("irc.connection")
    def test_learn_on_message(self, c, learn, reply, stripnicks):
        mod = pyborg.mod.mod_irc.ModIRC(pyborg.pyborg.pyborg, self.settings)
        src = mock.Mock()
        src.nick.return_value = "foobar"
        our_event = irc.client.Event(type=None, source=src, target=u"#ranarchism", arguments=[u"Hello Pyborg"])
        mod.on_pubmsg(c, our_event)
        learn.assert_called_with(our_event.arguments[0].encode("utf-8"))

    @mock.patch("pyborg.mod.mod_irc.ModIRC.strip_nicks", side_effect=lambda x, _: x)
    @mock.patch("pyborg.mod.mod_irc.ModIRC.reply")
    @mock.patch("pyborg.mod.mod_irc.ModIRC.learn")
    @mock.patch("irc.connection")
    def test_nick_reply(self, c, learn, reply, stripnicks):
        mod = pyborg.mod.mod_irc.ModIRC(pyborg.pyborg.pyborg, self.settings)
        # nick = mod.connection.get_nickname()
        nick = "steve"
        # c.get_nickname.return_value = "steve"
        mod.connection.real_nickname = nick
        src = mock.Mock()
        src.nick.return_value = "foobar"
        our_event = irc.client.Event(type=None, source=src, target=None, arguments=[u"%s: yolo swagins" % nick])
        mod.on_pubmsg(c, our_event)
        learn.assert_called_with(our_event.arguments[0].split(":")[1].encode("utf-8"))
        reply.assert_called_with(b" yolo swagins")

    @mock.patch("pyborg.mod.mod_irc.ModIRC.strip_nicks", side_effect=lambda x, _: x)
    @mock.patch("pyborg.mod.mod_irc.ModIRC.reply")
    @mock.patch("pyborg.mod.mod_irc.ModIRC.learn")
    @mock.patch("irc.connection")
    def test_ignore_reply(self, c, learn, reply, stripnicks):
        mod = pyborg.mod.mod_irc.ModIRC(pyborg.pyborg.pyborg, self.settings)
        # nick = mod.connection.get_nickname()
        nick = "steve"
        # c.get_nickname.return_value = "steve"
        mod.connection.real_nickname = nick
        src = mock.Mock()
        src.nick = "title"
        our_event = irc.client.Event(type=None, source=src, target="#ranarchism", arguments=[u"yolo swagins"])
        mod.on_pubmsg(c, our_event)
        learn.assert_not_called()
        reply.assert_not_called()

    @mock.patch("random.choice")
    def test_nick_replace(self, patched_choice):
        mod = pyborg.mod.mod_irc.ModIRC(pyborg.pyborg.pyborg, self.settings)
        our_event = irc.client.Event(type=None, source=None, target="#botally")
        mocked_channel = mock.Mock()
        patched_choice.return_value = "jrabbit"
        mod.channels = {"#botally": mocked_channel}
        msg = "#nick is the best bot maker!"
        output = mod.replace_nicks(msg, our_event)
        mocked_channel.users.assert_called_with()
        self.assertEqual(output, "jrabbit is the best bot maker!")

    def test_nick_strip(self):
        mod = pyborg.mod.mod_irc.ModIRC(pyborg.pyborg.pyborg, self.settings)
        our_event = irc.client.Event(type=None, source=None, target="#botally")
        mocked_channel = mock.Mock()
        mocked_channel.users.return_value = ["jrabbit"]
        mod.channels = {"#botally": mocked_channel}
        msg = "jrabbit is the best bot maker!"
        self.assertEqual(mod.strip_nicks(msg, our_event), "#nick is the best bot maker!")


@unittest.skip("idk why this has been disabled - 2019")
class TestLaunch(unittest.TestCase):
    settings = {
        "multiplex": True,
        "nickname": "PyBorg",
        "password": "",
        "quitmsg": "Bye :-(",
        "realname": "Pyborg",
        "reply2ignored": False,
        "server": {
            "channels": [
                {"chan": "#ranarchism", "reply_chance": 5, "speaking": True},
                {"chan": "#queertoo", "reply_chance": 5, "speaking": False},
            ],
            "ignorelist": [],
            "owners": ["jrabbit"],
            "port": 6697,
            "server": "chat.freenode.net",
            "ssl": True,
        },
        "speaking": True,
        "speakingchans": ["#test"],
        "stealth": False,
    }

    @mock.patch("pyborg.mod.mod_irc.check_server")
    @mock.patch("toml.load")
    @mock.patch("pyborg.pyborg.pyborg")
    @mock.patch("pyborg.mod.mod_irc.ModIRC")
    def test_launch(self, patched_pyb_irc, patched_pyb, patched_load, patched_check):
        patched_load.return_value = self.settings
        pyborg.mod.mod_irc.start_irc_bot()
        patched_pyb_irc.assert_called_with(patched_pyb, self.settings)
        patched_pyb_irc.return_value.start.assert_called_with()

    @mock.patch("pyborg.mod.mod_irc.check_server")
    @mock.patch("toml.load")
    @mock.patch("pyborg.mod.mod_irc.ModIRC")
    def test_ctrl_c(self, patched_pyb_irc, patched_load, patched_check):
        patched_pyb_irc.return_value.start.side_effect = KeyboardInterrupt
        patched_load.return_value = self.settings
        # with self.assertRaises(KeyboardInterrupt):
        pyborg.mod.mod_irc.start_irc_bot()
        patched_pyb_irc.return_value.teardown.assert_called_once_with()
        patched_pyb_irc.return_value.disconnect.assert_called_with("Killed at terminal.")

    @mock.patch("pyborg.mod.mod_irc.check_server")
    @mock.patch("toml.load")
    @mock.patch("pyborg.mod.mod_irc.ModIRC")
    def test_handle_exception(self, patched_pyb_irc, patched_load, patched_check):
        patched_pyb_irc.return_value.start.side_effect = Exception
        with self.assertRaises(Exception):
            pyborg.mod.mod_irc.start_irc_bot()
        # patched_pyb_irc.return_value.teardown.assert_called_once_with()
        patched_pyb_irc.return_value.disconnect.assert_called_with("Caught exception")
