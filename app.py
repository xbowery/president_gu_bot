import os
import logging
import random
import pymongo

from pymongo import MongoClient
from dotenv import load_dotenv

from telegram import Update, ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          Filters, CallbackContext)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv("./.env")
TOKEN = os.getenv("token")
MONGOURL = os.getenv("mongourl")
SECRETID = int(os.getenv("id"))
NAME = os.getenv("name")

client = MongoClient(MONGOURL)
db = client.jasonbot

USER_DB = db["user"]
PRAYER_DB = db["prayers"]


def init_settings(update, context):
    user = update.effective_user

    database_settings = USER_DB.find_one(
        {"_id": user.id}
    )

    count = 0

    if (database_settings is not None):
        count = database_settings["Pray Count"]

    chat_settings = {
        "_id": user.id,
        "First Name": user.first_name,
        "Last Name": user.last_name,
        "Username": user.username,
        "Pray Count": count
    }

    context.chat_data["chat_settings"] = chat_settings
    update_obj = {"$set": chat_settings}
    USER_DB.update_one(
        {"_id": user.id}, update_obj, upsert=True
    )


def start(update: Update, context: CallbackContext):
    if (update.message.chat_id == SECRETID):
        update.message.reply_text('Hi President Jason Gu Yao Chen')
        file1 = "assets/pic1.jpg"
        update.message.reply_photo(photo=open(file1, 'rb'))
        update.message.reply_text('All hail President Jason Gu Yao Chen')
        file2 = "assets/pic2.jpg"
        update.message.reply_photo(photo=open(file2, 'rb'))
    else:
        update.message.reply_text(
            'Hi, please pay your respects to our President Jason Gu Yao Chen.')
        file1 = "assets/pic1.jpg"
        update.message.reply_photo(photo=open(file1, 'rb'))
        update.message.reply_text('All hail President Jason Gu Yao Chen')
        file2 = "assets/pic2.jpg"
        update.message.reply_photo(photo=open(file2, 'rb'))
        update.message.reply_text(
            'Drop him a text @nineliejasongug on Telegram!')

    init_settings(update, context)


def pray(update: Update, context: CallbackContext):
    init_settings(update, context)
    user = update.effective_user

    user_record = USER_DB.find_one(
        {"_id": user.id}
    )
    user_record['Pray Count'] += 1

    prayer = PRAYER_DB.find_one(
        {"_id": NAME}
    )
    prayer['Pray Count'] += 1
    prayer_count = prayer['Pray Count']

    photo_dict = {1: 'pic1.jpg', 2: 'pic2.jpg', 3: 'pic3.jpg',
                  4: 'pic4.jpg', 5: 'pic5.png', 6: 'pic6.png', 7: 'pic7.png'}
    number = random.randint(1, len(photo_dict))
    filename = 'assets/' + photo_dict[number]

    update.message.reply_photo(photo=open(filename, 'rb'))

    update.message.reply_text(
        'Thanks for paying your respects to our President Jason Gu Yao Chen.')

    msg = f"""Our LORD AND SUPREME LEADER, PRIDE OF SMU CS, \
RIGHT HAND MAN OF YEOW LEONG, THE ONE AND ONLY PRESIDENT JASON GU YAOCHEN \
has been paid respects for a total of **{prayer_count}** times!"""

    update.message.reply_text(
        msg,
        parse_mode=ParseMode.MARKDOWN)

    if (prayer['Pray Count'] % 100 == 0):
        update.message.reply_text(
            f"""CONGRATULATIONS ON BEING THE PERSON \
            WHO PRAYED FOR THE {prayer_count}TH TIME!""")

        update.message.reply_text(
            'President Jason Gu loves you many many. 😘😘😘')
        update.message.reply_audio(audio=open('prize1.mp3', 'rb'))
        update.message.reply_audio(audio=open('prize2.mp3', 'rb'))

    update_prayer_obj = {"$set": prayer}
    update_user_obj = {"$set": user_record}

    PRAYER_DB.update_one(
        {"_id": NAME},
        update_prayer_obj,
        upsert=True
    )

    USER_DB.update_one(
        {"_id": user.id},
        update_user_obj,
        upsert=True
    )


def leaderboard(update: Update, context: CallbackContext):
    init_settings(update, context)
    msg = "**Current Leaderboard (Top 10 Users):**\n\n"

    count = USER_DB.estimated_document_count()
    if count > 10:
        count = 10
    top_users_cur = USER_DB.find({"Pray Count": { "$gt": 0 }}).sort("Pray Count", pymongo.DESCENDING).limit(10)

    for i in range(count):
        user = top_users_cur[i]

        first_name = user["First Name"] if user["First Name"] is not None else ""
        last_name = user["Last Name"] if user["Last Name"] is not None else ""
        username = "@" + user["Username"] if user["Username"] is not None else "No username"
        pray_count = user["Pray Count"]

        msg += f"{i+1}. {first_name} {last_name} ({username}): {pray_count} {'times' if pray_count > 1 else 'time'}\n"

    update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


def help(update: Update, context: CallbackContext):
    init_settings(update, context)

    msg = """/start - Starts this bot
/pray - Pay your respects to our President Jason Gu Yaochen
/leaderboard - Displays the leaderboard for users who prayed the most
    """

    update.message.reply_text(msg)


def error(update: Update, context: CallbackContext):
    '''Log Errors caused by Updates'''
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("pray", pray))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("leaderboard", leaderboard))
    dp.add_handler(MessageHandler(Filters.text, start))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
