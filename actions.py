'''
Api Bot actions.
'''

#!/usr/bin/python3
from telegram.bot import Bot
from telegram.chataction import ChatAction
from telegram.error import TelegramError
import requests
import config
from mastodon import Mastodon

if config.mastodon_instance:
    mastodon = Mastodon(client_id = 'pytooter_clientcred.secret',api_base_url=config.mastodon_instance)
    mastodon.log_in(
        config.mastodon_login,
        config.mastodon_password,
        to_file = 'pytooter_usercred.secret'
    )

def id(bot,update):
    '''
    response /id . may for development purpose.
    use /id
    '''
    print(update)
    bot.sendMessage(chat_id=update.channel_post.chat_id,
                    text="This channel's ID is {}".format(chatid))

def join_chat(bot,update):
    '''response when the bot join chat.'''
    id(bot,update)

def getme(bot,update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="I am {}".format(bot.getMe().id))

def start(bot,update):
    if not config.bot:
        getme(bot,update)

def upload(file_id,mime_type):
    file = requests.get(url=bot.get_file(file_id).file_path).content
    return mastodon.media_post(media_file=file, mime_type=mime_type)['id']

def elimage(bot,update,file_id):
    path=requests.get(url=bot.get_file(file_id).file_path).content
    files = {'name': path}
    try:
        text=requests.post(url="https://img.yoitsu.moe",files=files).text
    except requests.exceptions.RequestException as err:
        raise ValueError("Failed to process request:"+str(err))
    else:
        return text

def photo(bot,update):
    file_id = upload(file_id=update.channel_post.photo[-1].file_id, mime_type="image/jpeg")['id']
    text = update.channel_post.caption
    print(mastodon.status_post(status=text,media_ids=[file_id]))

def video(bot,update):
    print(update)
    #upload(bot,update,update.channel_post.photo[0].file_id)

def document(bot,update):
    try:
        text = elimage(bot,update,update.channel_post.document.file_id)
    except ValueError as err:
        print(str(err))
    else:
        print(mastodon.toot("{} {}".format(text,update.channel_post.caption)))

def updates(bot,update):
    print(update)

def text(bot,update):
    message = update.channel_post.text
    print(mastodon.toot(message))