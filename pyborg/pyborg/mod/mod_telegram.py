import logging
from functools import partial

import toml
import pyborg.pyborg
import pyborg.commands
import requests

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logger = logging.getLogger(__name__)

class Registry(object):
    """Command registry of decorated pyborg commands"""

    def __init__(self, mod_irc):
        self.registered = {}
        self.mod_irc = mod_irc

    def add(self, name, ob, internals, pass_msg):
        if internals:
            self.registered[name] = partial(ob, self.mod_irc.settings["multiplex"], multi_server="http://localhost:2001/")
        else:
            self.registered[name] = ob


class ModTelegram:
    def __init__(self, toml_file="telegram.toml"):
        self.settings = toml.load(toml_file)
        try:
            self.multiplexing = self.settings['pyborg']['multiplex']
            self.multi_server = self.settings['pyborg']['multiplex_server']
            self.multi_port = self.settings['pyborg']['multiplex_port']
        except KeyError:
            logger.info("Missing config key, you get defaults.")

        self.reply_rate = 100

        if not self.multiplexing:
            self.pyborg = pyborg.pyborg.pyborg()
        else:
            self.serverUrl = "http://{}:{}".format(self.multi_server, self.multi_port)
            self.pyborg = None

        # Telegram Commands setup
        self.registry = Registry(self)

    def start(self):
        """Start the bot."""
        # Create the Updater and pass it your bot's token.
        # Make sure to set use_context=True to use the new context based callbacks
        # Post version 12 this will no longer be necessary
        updater = Updater(self.settings['telegram']['token'], use_context=True)

        # Get the dispatcher to register handlers
        dp = updater.dispatcher

        # on different commands - answer in Telegram
        # dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("help", self.on_help))
        dp.add_handler(CommandHandler("reply_rate", self.on_admin_command))
        dp.add_handler(CommandHandler("info", self.on_admin_command))
        dp.add_handler(CommandHandler("known", self.on_admin_command))

        # on noncommand i.e message - echo the message on Telegram
        dp.add_handler(MessageHandler(Filters.text, self.on_echo))

        # log all errors
        dp.add_error_handler(self.on_error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()

    def on_error(self, update: Updater, context) -> None:
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    def on_admin_command(self, update: Updater, context) -> None:
        message = update.message.text
        if update.message.from_user.username in self.settings['telegram']['admins']:
            parts = message.split(' ')

            if parts[0] == '/reply_rate' and len(parts) > 1:
                self.reply_rate = int(parts[1])
                update.message.reply_text("New rate: {}".format(self.reply_rate))
            if parts[0] == '/info':
                resp = requests.get("{}/info".format(self.serverUrl))
                update.message.reply_text(resp.text)
            if parts[0] == '/known' and len(parts) > 1:
                word = parts[1]
                resp = requests.get("{}/known?word={}".format(self.serverUrl, word))
                update.message.reply_text(resp.text)
            # if parts[0] == '/replace' and len(parts) > 2:
            #     self.pyborg.replace(parts[1], parts[2])

    def on_help(self, update: Updater, context) -> None:
        """Send a message when the command /help is issued."""
        update.message.reply_text('Commands: `/reply_rate`, `/info`, `/known`.')

    def on_echo(self, update: Updater, context) -> None:
        """Echo the user message."""
        body = update.message.text

        username = update.message.from_user.first_name

        diff = 0
        for entity in update.message.entities:
            offset = entity.offset - diff
            length = entity.length
            diff = length - 5
            body = body[0:offset] + "#nick" + body[(offset+length):]

        if self.multiplexing:
            d = {"body": body, "reply_rate": self.reply_rate, "learning": 1, "owner": 1}
            resp = requests.post("{}/process".format(self.serverUrl), data=d)

            if resp.status_code == requests.codes.ok:
                if resp.text:
                    reply = resp.text.replace("#nick", username)
                    # update.message.reply_text(reply)
                    context.bot.send_message(
                        chat_id=update.message.chat.id,
                        text=reply
                    )
            else:
                logger.error(resp)
        else:
            resp = self.pyborg.reply(body)
            reply = resp.text.replace("#nick", username)
            context.bot.send_message(
                chat_id=update.message.chat.id,
                text=reply
            )

    def teardown(self) -> None:
        pass