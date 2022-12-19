import json
import os
import logging
import random
import pymongo
import requests
import validators

from pymongo import MongoClient
from dotenv import load_dotenv

from telegram import Update, ParseMode
from telegram.ext import (Updater, CommandHandler, MessageHandler,
                          ConversationHandler, Filters, CallbackContext)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv("./.env")
TOKEN = os.getenv("token")
MONGOURL = os.getenv("mongourl")
SECRETID = int(os.getenv("id"))
USER1 = int(os.getenv("user1"))
USER2 = int(os.getenv("user2"))
NAME = os.getenv("name")
API_URL = os.getenv("apiurl")
API_KEY = os.getenv("apikey")
MONGODB_NAME = os.getenv("database")
MONGODB_DATASOURCE = os.getenv("dataSource")

client = MongoClient(MONGOURL)
db = client.jasonbot

AUTHORISED_USERS = [SECRETID, USER1, USER2]

USER_DB = db["user"]
PRAYER_DB = db["prayers"]
ASSETS_DB = db["assets"]


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
    cursor = ASSETS_DB.find()

    if (update.message.chat_id == SECRETID):
        update.message.reply_text('Hi President Jason Gu Yao Chen')
        file1 = cursor.__getitem__(0)["url"]
        update.message.reply_photo(photo=str(file1))
        update.message.reply_text('All hail President Jason Gu Yao Chen')
        file2 = cursor.__getitem__(1)["url"]
        update.message.reply_photo(photo=str(file2))
    else:
        update.message.reply_text(
            'Hi, please pay your respects to our President Jason Gu Yao Chen.')
        file1 = cursor.__getitem__(0)["url"]
        update.message.reply_photo(photo=file1)
        update.message.reply_text('All hail President Jason Gu Yao Chen')
        file2 = cursor.__getitem__(1)["url"]
        update.message.reply_photo(photo=file2)
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

    count = ASSETS_DB.estimated_document_count()
    cursor = ASSETS_DB.find()

    number = random.randint(0, count-1)
    filename = cursor.__getitem__(number)["url"]

    update.message.reply_photo(photo=filename)

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

        update.message.reply_text(
            'President Jason Gu loves you many many. 😘😘😘')
        update.message.reply_audio(audio=open('assets/prize1.mp3', 'rb'))
        update.message.reply_audio(audio=open('assets/prize2.mp3', 'rb'))


def leaderboard(update: Update, context: CallbackContext):
    init_settings(update, context)
    msg = "Current Leaderboard (Top 10 Users):\n\n"

    count = USER_DB.estimated_document_count()
    if count > 10:
        count = 10
    top_users_cur = USER_DB.find({"Pray Count": {"$gt": 0}}).sort(
        "Pray Count", pymongo.DESCENDING).limit(10)

    for i in range(count):
        user = top_users_cur.__getitem__(i)

        first_name = user["First Name"] if user["First Name"] is not None \
            else ""
        last_name = user["Last Name"] if user["Last Name"] is not None else ""
        username = "@" + \
            user["Username"] if user["Username"] is not None else "No username"
        pray_count = user["Pray Count"]

        msg += f"{i+1}. {first_name} {last_name} ({username}): {pray_count} \
{'times' if pray_count > 1 else 'time'}\n"

    update.message.reply_text(msg)


def individual_prayer(update: Update, context: CallbackContext):
    init_settings(update, context)

    user = update.effective_user

    database_settings = USER_DB.find_one(
        {"_id": user.id}
    )

    count = database_settings["Pray Count"]

    msg = f"You have /pray-ed a total of <b>{count} times!</b> \n\n Keep /pray-ing!"

    update.message.reply_text(msg, parse_mode=ParseMode.HTML)


def init_add_pictures(update: Update, context: CallbackContext):
    user = update.effective_user

    if (user.id not in AUTHORISED_USERS):
        return

    msg = "Please send me a message containing the URL of the picture."

    update.message.reply_text(msg)
    return 1


def add_pictures(update: Update, context: CallbackContext):
    if (validators.url(update.message.text)):
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Request-Headers': '*',
            'api-key': API_KEY
        }

        payload = json.dumps({
            "collection": "assets",
            "database": MONGODB_NAME,
            "dataSource": MONGODB_DATASOURCE,
            "document": {
                "url": update.message.text
            }
        })

        response = requests.request("POST", API_URL, headers=headers, data=payload)
        if (response.status_code == 201):
            update.message.reply_text("Picture successfully added!")
        else:
            msg = "There is an error while inserting into the database. Please try again later."
            update.message.reply_text(msg)

        return ConversationHandler.END
    else:
        msg_one = "Sorry, you have entered an invalid URL."
        msg_two = "Please send me a message containing the URL of the picture."
        update.message.reply_text(msg_one)
        update.message.reply_text(msg_two)
        return 1


def end(update, context):
    chat_id = update.message.chat.id

    context.bot.send_message(
        chat_id=chat_id,
        text="Action cancelled."
    )
    return ConversationHandler.END


def help(update: Update, context: CallbackContext):
    init_settings(update, context)

    msg = """/start - Starts this bot
/pray - Pay your respects to our President Jason Gu Yaochen
/leaderboard - Displays the leaderboard for users who prayed the most
/get_pray_count - Displays your individual /pray count
    """

    update.message.reply_text(msg)


def error(update: Update, context: CallbackContext):
    '''Log Errors caused by Updates'''
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    add_pictures_conv = ConversationHandler(
        entry_points=[CommandHandler("add_picture", init_add_pictures)],
        states={
            1: [
                CommandHandler("end", end),
                MessageHandler(Filters.text, add_pictures)
            ],
        },
        fallbacks=[CommandHandler("end", end)],
        allow_reentry=True
    )
    dp.add_handler(add_pictures_conv)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("pray", pray))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("get_pray_count", individual_prayer))
    dp.add_handler(CommandHandler("leaderboard", leaderboard))
    dp.add_handler(MessageHandler(Filters.text, start))

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
