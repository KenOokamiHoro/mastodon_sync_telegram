'''
Api Bot actions.
'''

#!/usr/bin/python3
from telegram.bot import Bot
from telegram.chataction import ChatAction
from telegram.error import TelegramError
import config
import requests
import twitter
from mastodon import Mastodon

if config.mastodon_instance:
    mastodon = Mastodon(client_id='pytooter_clientcred.secret',
                        api_base_url=config.mastodon_instance)
    mastodon.log_in(
        config.mastodon_login,
        config.mastodon_password,
        to_file='pytooter_usercred.secret'
    )

if config.twitter_consumer_key:
    twitter_instance = twitter.Api(consumer_key=config.twitter_consumer_key,
                                   consumer_secret=config.twitter_consumer_secret,
                                   access_token_key=config.twitter_access_token_key,
                                   access_token_secret=config.twitter_access_token_secret)


def id(bot, update):
    '''response /id . may for development purpose.'''
    print(update)
    bot.sendMessage(chat_id=update.channel_post.chat_id,
                    text="This channel's ID is {}".format(chatid))


def join_chat(bot, update):
    '''response when the bot join chat.'''
    id(bot, update)


def getme(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="I am {}".format(bot.getMe().id))


def start(bot, update):
    if not config.bot:
        getme(bot, update)


def upload(bot, file_id, mime_type):
    file = requests.get(url=bot.get_file(file_id).file_path).content
    return mastodon.media_post(media_file=file, mime_type=mime_type)


def elimage(bot, update, file_id):
    path = requests.get(url=bot.get_file(file_id).file_path).content
    files = {'name': path}
    try:
        text = requests.post(url="https://img.yoitsu.moe", files=files).text
    except requests.exceptions.RequestException as err:
        raise ValueError("Failed to process request:" + str(err))
    else:
        return text


def getauthor(update):
    if update.channel_post.forward_from:
        return ' '.join(["↩️",
                         update.channel_post.forward_from.first_name,
                         update.channel_post.forward_from.last_name])
    else:
        return ' '.join([update.channel_post.from_user.first_name,
                         update.channel_post.from_user.last_name])


def photo(bot, update):
    if update.channel_post:
        file = upload(bot=bot,
                      file_id=update.channel_post.photo[-1].file_id,
                      mime_type="image/jpeg")
        file_id = file['id']
        file_url = file['url']
        text = "{}: {}".format(getauthor(update), update.channel_post.caption)
        print(mastodon.status_post(status=text, media_ids=[file_id]))
        print(twitter_instance.PostUpdate(status=text, media=file_url))


def video(bot, update):
    print(update)
    # upload(bot,update,update.channel_post.photo[0].file_id)


def document(bot, update):
    if update.channel_post:
        try:
            text = elimage(bot, update, update.channel_post.document.file_id)
        except ValueError as err:
            print(str(err))
        else:
            message = "{}: {} {}".format(
                getauthor(update), text, update.channel_post.caption)
            print(mastodon.toot(message))
            print(twitter_instance.PostUpdate(status=message))


def updates(bot, update):
    print(update)


def text(bot, update):
    if update.channel_post:
        print(update)
        message = "{}: {}".format(getauthor(update), update.channel_post.text)
        mastodon_url = mastodon.toot(message)['url']
        if len(message) > 140:
            tips = "\nView on Mastodon: {}".format(mastodon_url)
            twitter_message = message[:139 - len(tips)] + tips
            print(twitter_instance.PostUpdate(status=twitter_message))
        else:
            print(twitter_instance.PostUpdate(status=message))
