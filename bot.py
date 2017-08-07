#!/usr/bin/python
# -*- coding: utf-8 -*-

from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler
from telegram.ext import Job
from telegram.ext.filters import Filters
from telegram.bot import Bot
from telegram.chataction import ChatAction
import logging
import config
import actions
import filters
import sys


class TransferBot:
    def __init__(self):
        # Setting up bot
        self.updater = Updater(token=config.token)
        self.job_queue = self.updater.job_queue
        self.dispatcher = self.updater.dispatcher
        self.botObj = Bot(token=config.token)
        # Register handlers
        # self.dispatcher.add_handler(MessageHandler(Filters.video,actions.video))
        self.dispatcher.add_handler(MessageHandler(
            Filters.photo, actions.photo))
        self.dispatcher.add_handler(MessageHandler(
            Filters.document, actions.document))
        self.dispatcher.add_handler(MessageHandler(
            Filters.text, actions.text))
        self.dispatcher.add_handler(CommandHandler('start', actions.start))
        self.dispatcher.add_handler(CommandHandler('id', actions.id))
        self.dispatcher.add_handler(CommandHandler('getme', actions.getme))
        if config.horo:
            self.job_queue.run_repeating(actions.fetch_kenookamihoro_mastodon,
                                         interval=600, first=10,
                                         context={'mastodon': 6669492})
            self.job_queue.run_repeating(actions.fetch_kenookamihoro_twitter,
                                         interval=600, first=0,
                                         context={'twitter': 893061160550793216})
        # self.dispatcher.add_handler(MessageHandler(
        #    filters.always_true, actions.updates))
        # Start bot

    def start(self):
        self.updater.start_polling()


if __name__ == "__main__":
    # import bot components
    try:
        import config
    except ImportError:
        print("Please create config file 'config.py' first.")
        exit(1)

    logging.basicConfig(stream=sys.stderr,
                        format='%(message)s', level=logging.INFO)
    transfer = TransferBot()
    transfer.start()
