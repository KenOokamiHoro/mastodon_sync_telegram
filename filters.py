'''Filters'''
import config

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

def current_channel(update):
    try:
        return str(update.channel_post.chat.id) == config.channel
    except AttributeError:
        return False