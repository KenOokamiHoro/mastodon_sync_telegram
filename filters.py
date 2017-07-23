'''Filters'''
import config
from telegram.ext import BaseFilter


def me_join_chat(update):
    try:
        print(str(update.new_chat_member.id))
        if str(update.new_chat_member.id) == config.bot:
            return True
        else:
            return False
    except AttributeError:
        return False


def always_true(update):
    return True
