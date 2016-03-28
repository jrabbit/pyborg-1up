import ssl


import baker
import irc.bot
import irc.strings
import irc
import toml

import pyborg.pyborg


class ModIRC(irc.bot.SingleServerIRCBot):

    def __init__(self, my_pyborg, channel, nickname, server, port, **connect_params):
        self.settings = toml.load("example.irc.toml")
        server = self.settings['server']['server']
        port = self.settings['server']['port']
        nickname = self.settings['nickname']
        realname = self.settings['realname']
        super(ModIRC, self).__init__(
            [(server, port)], nickname, realname, **connect_params)
        self.my_pyborg = my_pyborg
        self.channel = channel

    def on_welcome(self, c, e):
        for chan_dict in self.settings['server']['channels']:
            c.join(chan_dict['chan'])

    def on_pubmsg(self, c, e):
        a = e.arguments[0].split(":", 1)
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
            self.do_command(e, a[1].strip())
        return

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection
        c.notice(nick, "Hello {}".format(nick))


@baker.command(default=True)
def start_irc_bot(channel, nickname, server, port=6697):
    pyb = pyborg.pyborg.pyborg()
    ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
    bot = ModIRC(pyb, channel, nickname, server, port, connect_factory=ssl_factory)
    try:
        bot.start()
    except KeyboardInterrupt:
        pyb.save_all()
        bot.disconnect("Default disconnect message")

if __name__ == '__main__':
    baker.run()
