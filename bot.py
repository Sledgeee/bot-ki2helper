import os
import random
import db
import pytz
from datetime import datetime
from bson import ObjectId
from telebot import TeleBot
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from utils import format_dt


HELPER_BOT_TOKEN = os.getenv("HELPER_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID_TEST")
APP_CONFIG_ID = os.getenv("APP_CONFIG_ID")
bot = TeleBot(HELPER_BOT_TOKEN, threaded=False)


def get_status():
    helper_health = db.health.get("helper")
    return helper_health["status"]


@bot.message_handler(commands=['start'])
def start_cmd(message: Message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Розклад 📅", callback_data="schedule"),
        InlineKeyboardButton("Плейліст 🎥", callback_data="playlist")
    )
    markup.row(InlineKeyboardButton("Посилання на Zoom 🔗", callback_data="zoom"))
    markup.row(InlineKeyboardButton("Графік проведення пар ⏰", callback_data="timetable"))
    markup.row(InlineKeyboardButton("Який зараз тиждень ❔", callback_data="week"))
    markup.row(InlineKeyboardButton("Отримати всі доступні команди 🆘", callback_data="help"))
    bot.send_message(message.chat.id, 'Обери, що потрібно:', reply_markup=markup)


@bot.message_handler(commands=['help'])
def help_cmd(message: Message):
    cmds = bot.get_my_commands()
    help_msg = ""
    for cmd in cmds:
        help_msg += f"/{cmd.command} - {cmd.description}\n"
    bot.send_message(message.chat.id, help_msg)


@bot.message_handler(commands=['playlist'])
def playlist_cmd(message: Message):
    items = list(db.playlist.find({}, {"_id": 0}))
    bot.send_message(message.chat.id, items[-1]['link'])


@bot.message_handler(commands=['playlists'])
def playlists_cmd(message: Message):
    items = db.playlist.find({}, {"_id": 0})
    playlists = ""
    for i, item in enumerate(items):
        playlists += f"№{i + 1}: {item['link']}\n"
    bot.send_message(message.chat.id, playlists)


@bot.message_handler(commands=['timetable'])
def timetable_cmd(message: Message):
    if db.timetable.count_documents({}) == 0:
        bot.send_message(message.chat.id, 'Графік проведення пар ще не додано')
    else:
        items = db.timetable.find({}, {"_id": 0}).sort("number")
        timetable = ""
        for item in items:
            lesson_number = f"№{item['number']}:"
            start = \
                f"{format_dt(item['start_hour'])}:{format_dt(item['start_minute'])}-" \
                f"{format_dt(item['end_hour'])}:{format_dt(item['end_minute'])}"
            break_str = f"(перерва {item['break']} хв)" if item['break'] > 0 else ""
            timetable += f"{lesson_number} {start} {break_str}\n"
        bot.send_message(message.chat.id, timetable)


@bot.message_handler(commands=['week'])
def week_cmd(message: Message):
    bot.send_message(message.chat.id, db.week.find_one({}, {"_id": 0})['type'])


@bot.message_handler(commands=['zoom'])
def zoom_cmd(message: Message):
    if db.zoom.count_documents({}) == 0:
        bot.send_message(message.chat.id, 'Жодного посилання на пару ще не додано ⚠️')
    else:
        zoom_items = db.zoom.find()
        markup = InlineKeyboardMarkup()
        for item in zoom_items:
            lesson = db.lesson.find_one({"_id": item['lesson']}, {"_id": 0})
            teacher = db.teacher.find_one({"_id": lesson['teacher']}, {"_id": 0})
            markup.row(InlineKeyboardButton(
                text=f"{teacher['name']} ({lesson['short_name']} {lesson['type']})",
                callback_data=f"zoom_{item['_id']}"
            ))
        bot.send_message(message.chat.id, 'Оберіть потрібний предмет:', reply_markup=markup)


@bot.message_handler(commands=['schedule'])
def schedule_cmd(message: Message):
    if db.schedule.count_documents({}) == 0:
        bot.send_message(message.chat.id, 'Розклад ще не додано')
    else:
        week = (db.week.find_one({}, {"_id": 0}))["type"]
        schedule_items = db.schedule.find({"$or": [{"week": week}, {"week": "-"}]},
                                          {"_id": 0}).sort("number").sort("day_number")
        timetable_items = db.timetable.find({}, {"_id": 0}).sort("number")
        day = schedule_items[0]['day']
        schedule = f"<b>Цього тижня пари по {week}у\n{day}:</b>\n"

        for item in schedule_items:
            lesson = db.lesson.find_one({"_id": item["lesson"]})
            teacher = db.teacher.find_one({"_id": lesson["teacher"]})

            if day != item["day"]:
                day = item["day"]
                schedule += f"\n<b>{day}</b>:\n"

            schedule += \
                f"№{item['number']} ({format_dt(timetable_items[item['number'] - 1]['start_hour'])}:" \
                f"{format_dt(timetable_items[item['number'] - 1]['start_minute'])}): {lesson['type']} " \
                f"{lesson['name']}, {teacher['name']}\n"
        bot.send_message(message.chat.id, schedule, parse_mode='Html')


@bot.message_handler(commands=['schedule_today'])
def schedule_today_cmd(message: Message):
    if db.schedule.count_documents({}) == 0:
        bot.send_message(message.chat.id, 'Розклад ще не додано')
    else:
        week = (db.week.find_one({}, {"_id": 0}))["type"]
        timetable_items = db.timetable.find({}, {"_id": 0}).sort("number")
        now = datetime.now(tz=pytz.timezone('Europe/Kiev'))
        schedule_items = list(db.schedule.find({"day_number": now.weekday() + 1,
                                                "$or": [{"week": week}, {"week": "-"}]}, {"_id": 0}).sort("number"))
        if len(schedule_items) > 0:
            schedule = f"<b>Сьогодні {schedule_items[0]['day']}, пари по {week}у:</b>\n"
            for item in schedule_items:
                lesson = db.lesson.find_one({"_id": item["lesson"]})
                teacher = db.teacher.find_one({"_id": lesson["teacher"]})
                schedule += \
                    f"№{item['number']} ({format_dt(timetable_items[item['number'] - 1]['start_hour'])}:" \
                    f"{format_dt(timetable_items[item['number'] - 1]['start_minute'])}): {lesson['type']} " \
                    f"{lesson['name']}, {teacher['name']}\n"
            bot.send_message(message.chat.id, schedule, parse_mode='Html')
        else:
            bot.send_message(message.chat.id, 'Сьогодні немає пар 🤩')


@bot.message_handler(commands=['nearest'])
def nearest_cmd(message: Message):
    pass


@bot.message_handler(commands=['cock'])
def cock_cmd(message: Message):
    cock_size = random.randint(0, 50)
    reaction = "🫡" if cock_size == 50 else "🤩" if cock_size >= 35 else "😎" if cock_size >= 10 else "🧐"
    bot.send_message(message.chat.id, f"Твій 🐓 {cock_size} см {reaction}")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: CallbackQuery):
    if call.data == 'schedule':
        schedule_cmd(call.message)
    elif call.data == 'playlist':
        playlist_cmd(call.message)
    elif call.data == 'timetable':
        timetable_cmd(call.message)
    elif call.data == 'zoom':
        zoom_cmd(call.message)
    elif call.data == 'week':
        week_cmd(call.message)
    elif call.data == 'help':
        help_cmd(call.message)
    elif "zoom_" in call.data:
        zoom_id = call.data.split("_")[1]
        zoom = db.zoom.find_one({"_id": ObjectId(zoom_id)})
        lesson = db.lesson.find_one({"_id": zoom['lesson']})
        teacher = db.teacher.find_one({"_id": lesson['teacher']})
        bot.send_message(call.message.chat.id,
                         f"{teacher['name']} ({lesson['short_name']} {lesson['type']}): {zoom['link']}")
    bot.delete_message(call.message.chat.id, call.message.message_id)


user_commands = [
    BotCommand("/start", "Розпочати діалог з ботом"),
    BotCommand("/help", "Отримати список команд"),
    BotCommand("/playlist", "Отримати плейліст за поточний семестр"),
    BotCommand("/playlists", "Отримати всі доступні плейлісти"),
    BotCommand("/timetable", "Отримати графік початку та кінця пар"),
    BotCommand("/week", "Який зараз тиждень"),
    BotCommand("/zoom", "Отримати посилання на Zoom"),
    BotCommand("/schedule", "Отримати розклад пар на тижден"),
    BotCommand("/schedule_today", "Отримати розклад пар на сьогоднішній день"),
    BotCommand("/nearest", "Отримати найближчу пару та час до її початку"),
    BotCommand("/cock", "🐓")
]
bot.set_my_commands(commands=user_commands)
