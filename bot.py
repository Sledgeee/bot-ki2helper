import os
import random
from telebot import TeleBot
from telebot.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from utils import format_dt, api_request

HELPER_BOT_TOKEN = os.getenv("HELPER_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = TeleBot(HELPER_BOT_TOKEN, threaded=False)


@bot.message_handler(commands=["start"])
def start_cmd(message: Message):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("Повний розклад 📅", callback_data="schedule"))
    markup.row(InlineKeyboardButton("Сьогоднішній розклад 📅", callback_data="schedule_today"))
    markup.row(InlineKeyboardButton("Плейліст 🎥", callback_data="playlist"))
    markup.row(InlineKeyboardButton("Посилання на Zoom 🔗", callback_data="zoom"))
    markup.row(InlineKeyboardButton("Взнати номер аудиторії на пару ❔", callback_data="cabinet"))
    markup.row(InlineKeyboardButton("Графік проведення пар ⏰", callback_data="timetable"))
    markup.row(InlineKeyboardButton("Який зараз тиждень ❔", callback_data="week"))
    markup.row(InlineKeyboardButton("Отримати всі доступні команди 🆘", callback_data="help"))
    bot.send_message(message.chat.id, 'Обери, що потрібно:', reply_markup=markup)


@bot.message_handler(commands=["help"])
def help_cmd(message: Message):
    cmds = bot.get_my_commands()
    help_msg = ""
    for cmd in cmds:
        help_msg += f"/{cmd.command} - {cmd.description}\n"
    bot.send_message(message.chat.id, help_msg)


@bot.message_handler(commands=["playlist"])
def playlist_cmd(message: Message):
    items = api_request('get', 'crud/playlists')
    bot.send_message(message.chat.id, items[-1]['link'])


@bot.message_handler(commands=["playlists"])
def playlists_cmd(message: Message):
    items = api_request('get', 'crud/playlists')
    playlists = ""
    for i, item in enumerate(items):
        playlists += f"№{i + 1}: {item['link']}\n"
    bot.send_message(message.chat.id, playlists)


@bot.message_handler(commands=["timetable"])
def timetable_cmd(message: Message):
    items = api_request('get', 'crud/timetable')[0]['items']
    if len(items) == 0:
        bot.send_message(message.chat.id, 'Графік проведення пар ще не додано ⚠️')
    else:
        timetable = ""
        for item in items:
            lesson_number = f"№{item['number']}:"
            start = \
                f"{format_dt(item['start_hour'])}:{format_dt(item['start_minute'])}-" \
                f"{format_dt(item['end_hour'])}:{format_dt(item['end_minute'])}"
            break_str = f"(перерва {item['break']} хв)" if item['break'] > 0 else ""
            timetable += f"{lesson_number} {start} {break_str}\n"
        bot.send_message(message.chat.id, timetable)


@bot.message_handler(commands=["week"])
def week_cmd(message: Message):
    week = api_request('get', 'crud/week')[0]
    bot.send_message(message.chat.id, week['type'])


@bot.message_handler(commands=["zoom"])
def zoom_cmd(message: Message):
    lessons = api_request('get', 'crud/lessons')
    if len(lessons) == 0:
        bot.send_message(message.chat.id, 'Жодної пари ще не додано ⚠️')
    else:
        markup = InlineKeyboardMarkup()
        for lesson in lessons:
            markup.row(InlineKeyboardButton(
                text=f"{lesson['short_name']} {lesson['type']} ({lesson['teacher']})",
                callback_data=f"zoom_{lesson['_id']}"
            ))
        bot.send_message(message.chat.id, 'Оберіть потрібний предмет:', reply_markup=markup)


@bot.message_handler(commands=["cabinet"])
def cabinet_cmd(message: Message):
    schedule = api_request('get', 'crud/schedule')
    if len(schedule) == 0:
        bot.send_message(message.chat.id, 'Жодної пари ще не додано ⚠️')
    else:
        markup = InlineKeyboardMarkup()
        for item in schedule:
            markup.row(InlineKeyboardButton(
                text=f"{item['lesson']['short_name']} {item['lesson']['type']} ({item['lesson']['teacher']})",
                callback_data=f"cab_{item['_id']}"
            ))
        bot.send_message(message.chat.id, 'Оберіть потрібний предмет:', reply_markup=markup)


@bot.message_handler(commands=["schedule"])
def schedule_cmd(message: Message):
    week = api_request('get', 'crud/week')[0]["type"]
    items = api_request('get', f'schedule/filtered/{week}')

    if len(items) == 0:
        bot.send_message(message.chat.id, 'Розклад ще не додано ⚠️')
    else:
        timetable_items = api_request('get', 'crud/timetable')[0]['items']
        day = items[0]['day']
        schedule = f"<b>Цього тижня пари по {week}у\n{day}:</b>\n"

        for item in items:
            if day != item["day"]:
                day = item["day"]
                schedule += f"\n<b>{day}</b>:\n"

            lesson = item['lesson']
            schedule += \
                f"№{item['number']} ({format_dt(timetable_items[item['number'] - 1]['start_hour'])}:" \
                f"{format_dt(timetable_items[item['number'] - 1]['start_minute'])}): {lesson['type']} " \
                f"{lesson['name']}, {lesson['teacher']}\n"
        bot.send_message(message.chat.id, schedule, parse_mode='Html')


@bot.message_handler(commands=["schedule_today"])
def schedule_today_cmd(message: Message):
    docs_count = api_request('get', 'schedule/count')
    if docs_count == 0:
        bot.send_message(message.chat.id, 'Розклад ще не додано ⚠️')
    else:
        week = api_request('get', 'crud/week')[0]["type"]
        items = api_request('get', f'schedule/filtered/today/{week}')
        if len(items) > 0:
            timetable_items = api_request('get', 'crud/timetable')[0]['items']
            schedule = f"<b>Сьогодні {items[0]['day']}, пари по {week}у:</b>\n"
            for item in items:
                lesson = item['lesson']
                schedule += \
                    f"№{item['number']} ({format_dt(timetable_items[item['number'] - 1]['start_hour'])}:" \
                    f"{format_dt(timetable_items[item['number'] - 1]['start_minute'])}): {lesson['type']} " \
                    f"{lesson['name']}, {lesson['teacher']}\n"
            bot.send_message(message.chat.id, schedule, parse_mode='Html')
        else:
            bot.send_message(message.chat.id, 'Сьогодні немає пар 🤩')


@bot.message_handler(commands=["nearest"])
def nearest_cmd(message: Message):
    result = api_request('get', 'schedule/nearest')
    bot.send_message(message.chat.id, result)


@bot.message_handler(commands=["cock"])
def cock_cmd(message: Message):
    cock_size = random.randint(0, 50)
    reaction = "🫡" if cock_size == 50 else "🤩" if cock_size >= 35 else "😎" if cock_size >= 10 else "🧐"
    bot.send_message(message.chat.id, f"Твій 🐓 {cock_size} см {reaction}")


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: CallbackQuery):
    if call.data == "schedule":
        schedule_cmd(call.message)
    elif call.data == "schedule_today":
        schedule_today_cmd(call.message)
    elif call.data == "playlist":
        playlist_cmd(call.message)
    elif call.data == "timetable":
        timetable_cmd(call.message)
    elif call.data == "zoom":
        zoom_cmd(call.message)
    elif call.data == "cabinet":
        cabinet_cmd(call.message)
    elif call.data == "week":
        week_cmd(call.message)
    elif call.data == "help":
        help_cmd(call.message)
    elif "zoom_" in call.data:
        lesson_id = call.data.split("_")[1]
        lesson = api_request('get', f'crud/lessons/{lesson_id}')
        bot.send_message(call.message.chat.id,
                         f"{lesson['short_name']} {lesson['type']} ({lesson['teacher']})\n"
                         f"Посилання: {lesson['zoom'] if lesson['zoom'] != '' else 'немає'}")
    elif "cab_" in call.data:
        item_id = call.data.split("_")[1]
        item = api_request('get', f'crud/schedule/{item_id}')
        lesson = item['lesson']
        bot.send_message(call.message.chat.id,
                         f"{lesson['short_name']} {lesson['type']} ({lesson['teacher']})\n"
                         f"Аудиторія: {item['cabinet'] if item['cabinet'] != '' else 'немає'}")
    bot.delete_message(call.message.chat.id, call.message.message_id)


user_commands = [
    BotCommand("/start", "Розпочати діалог з ботом"),
    BotCommand("/help", "Отримати список команд"),
    BotCommand("/playlist", "Отримати плейліст за поточний семестр"),
    BotCommand("/playlists", "Отримати всі доступні плейлісти"),
    BotCommand("/timetable", "Отримати графік початку та кінця пар"),
    BotCommand("/week", "Який зараз тиждень"),
    BotCommand("/zoom", "Отримати посилання на Zoom"),
    BotCommand("/cabinet", "Отримати номер кабінету пари"),
    BotCommand("/schedule", "Отримати розклад пар на тижден"),
    BotCommand("/schedule_today", "Отримати розклад пар на сьогоднішній день"),
    BotCommand("/nearest", "Отримати найближчу пару та час до її початку"),
    BotCommand("/cock", "🐓")
]
bot.set_my_commands(commands=user_commands)
