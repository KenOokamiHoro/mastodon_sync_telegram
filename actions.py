'''
Api Bot actions.
'''

#!/usr/bin/python3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.bot import Bot
from telegram.chataction import ChatAction
from telegram.error import TelegramError
import config
import datetime
import json
import requests
import re
import twitter
from bs4 import BeautifulSoup
from mastodon import Mastodon


if config.sender:
    mastodon = config.init_mastodon_instance(config.sender['mastodon'])
    twitter_instance = config.init_twitter_instance(config.sender['twitter'])

if config.horo:
    horo_mastodon = config.init_mastodon_instance(config.horo['mastodon'])
    horo_twitter_instance = config.init_twitter_instance(
        config.horo['twitter'])


def id(bot, update):
    '''response /id . may for development purpose.'''
    update.reply(text="This chat's ID is {}".format(chatid))


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
                         (update.channel_post.forward_from.last_name or '')])
    else:
        return ' '.join([update.channel_post.from_user.first_name,
                         (update.channel_post.from_user.last_name or '')])


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


def process_toots(bot, toots):
    for toot in toots:
        keyboard = [[InlineKeyboardButton("Link to author", url=toot['account']['url']),
                     InlineKeyboardButton("Link to this toot", url=toot['url'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = BeautifulSoup(toot['content'], 'html.parser').get_text()
        bot.sendMessage(chat_id=config.channel,
                        text="{}:\n{}".format(
                            toot['account']['display_name'], text),
                        reply_markup=reply_markup)


def fetch_kenookamihoro_mastodon(bot, job):
    toot_item = [item for item in horo_mastodon.timeline_home(since_id=job.context['mastodon'])
                 if 'Ken_Ookami_Horo' in item['account']['acct']]
    if toot_item:
        job.context['mastodon'] = max([item['id'] for item in toot_item])
        process_toots(bot, toot_item)


def get_original_tweet(tweet):
    original_tweet = None
    if tweet.get('urls') and "https://twitter.com" in tweet.get('urls'):
        original_tweet = horo_twitter_instance.GetStatus(
            status_id=tweet['urls'][0]['expanded_url'].split("/")[-1]).AsDict()
    elif tweet.get('retweeted'):
        original_tweet = horo_twitter_instance.GetStatus(
            status_id=tweet['retweeted_status']['id']).AsDict()
    elif tweet.get('in_reply_to_status_id'):
        original_tweet = horo_twitter_instance.GetStatus(
            status_id=tweet['in_reply_to_status_id']).AsDict()
    if original_tweet:
        return original_tweet
    else:
        raise KeyError("Not a reply/retweet/quote tweet.")


def make_tweet_keyboard(tweet, original_tweet=None):
    tweet_base_url = "https://twitter.com/{}/status/{}"
    user_base_url = "https://twitter.com/{}"
    keyboard = [[]]
    tweet_url = tweet_base_url.format(
        tweet['user']['screen_name'], tweet['id'])
    tweet_author = user_base_url.format(
        tweet['user']['screen_name'])
    keyboard[0].extend([
        InlineKeyboardButton("Author", url=tweet_author),
        InlineKeyboardButton("Tweet", url=tweet_url)])
    if original_tweet:
        original_tweet_url = tweet_base_url.format(
            original_tweet['user']['screen_name'], original_tweet['id'])
        original_tweet_author = user_base_url.format(
            original_tweet['user']['screen_name'])
        keyboard[0].extend([
            InlineKeyboardButton(
                "Original author", url=original_tweet_author),
            InlineKeyboardButton("Original tweet", url=original_tweet_url)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def process_tweets(bot, tweets):
    for tweet in tweets:
        if "(from Mastodon)" in tweet['text']:
            continue
        try:
            original_tweet = get_original_tweet(tweet)
        except KeyError:
            original_tweet = None
            text = "{}:\n{}".format(
                tweet['user']['name'],
                tweet['text']
            )
        else:
            text = "{} {} {}'s tweet:\n{}"
            if tweet.get('urls'):
                action = "quoted"
            elif tweet.get('in_reply_to_status_id'):
                action = "replied"
            elif tweet.get('retweeted'):
                action = "retweeted"
            text = text.format(
                tweet['user']['name'],
                action,
                original_tweet['user']['name'],
                tweet['text']
            )

        finally:
            reply_markup = make_tweet_keyboard(tweet, original_tweet)
            bot.sendMessage(chat_id=config.channel,
                            text=text,
                            reply_markup=reply_markup)


def fetch_kenookamihoro_twitter(bot, job):
    tweets = [item.AsDict()for item in horo_twitter_instance.GetUserTimeline(
        screen_name="Ken_Ookami_Horo", since_id=job.context['twitter'])]
    if tweets:
        job.context['twitter'] = tweets[0]['id']
        process_tweets(bot, tweets)


def process_notifications(bot, notifications):
    for notification in notifications:
        keyboard = [[InlineKeyboardButton("Author", url=notification['account']['url']),
                     InlineKeyboardButton(
                         "This toot", url=notification['status']['url']),
                     InlineKeyboardButton("Source toot", url=notification['status']['url'])]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = BeautifulSoup(notification['status']
                             ['content'], 'html.parser').get_text()
        bot.sendMessage(chat_id=config.channel,
                        text="{}:\n{}".format(
                            notification['account']['display_name'], text),
                        reply_markup=reply_markup)


def fetch_sender_mastodon_notifications(bot, job):
    notifications = [item for item in mastodon.notifications(since_id=job.context['mastodon'])
                     if item['type'] == 'mention']
    if notifications:
        job.context['mastodon'] = max([item['id'] for item in toot_item])
        process_notifications(bot, notifications)
