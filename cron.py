from bot import CHAT_ID, bot
from utils import format_dt, api_request
from pytz import timezone
from datetime import datetime


def check_birthday(now: datetime):
    if now.hour == 0 and now.minute == 0:
        birthday_items = api_request('get', 'crud/birthdays')
        now_formatted = f"{format_dt(now.day)}.{format_dt(now.month)}"
        for item in birthday_items:
            if item['date'] == now_formatted:
                bot.send_message(CHAT_ID, f"<b>{item['student_name']}</b> сьогодні святкує День Народження!",
                                 parse_mode='Html')
                bot.send_sticker(CHAT_ID, "CAACAgIAAxkBAAEG9LhjpKhQ2FUi31gbecql2Kr89xrLBQAChQIAAkGa3Q37oxVj75ZDnywE")


def check_schedule(now: datetime):
    if (now.hour == 7 and now.minute == 55) or 8 < now.hour < 20:
        week = api_request('get', 'crud/week')[0]['type']
        items = api_request('get', f'schedule/filtered/today/{week}')
        if len(items) == 0:
            return
        else:
            timetable_items = api_request('get', 'crud/timetable')[0]['items']
            for item in items:
                lesson = item['lesson']
                hour = timetable_items[item["number"] - 1]["start_hour"]
                minute = timetable_items[item["number"] - 1]["start_minute"] - 5
                if minute < 0:
                    hour -= 1
                    minute += 60
                if hour == now.hour and minute == now.minute:
                    bot.send_message(CHAT_ID, f"⚡️️️⚡️️⚡️ Через 5 хв розпочинається:\n{lesson['type']} {lesson['name']},"
                                              f" {lesson['teacher']}\nАудиторія: {item['cabinet']}\n"
                                              f"Посилання: {lesson['zoom'] if lesson['zoom'] != '' else 'немає'}")


def swap_week(now: datetime):
    if now.hour == 0 and now.minute == 0 and now.weekday() == 0:
        week = api_request('get', 'crud/week')[0]
        new_week = "Чисельник" if week["type"] == "Знаменник" else "Знаменник"
        api_request('put', f'crud/week/{week["_id"]}', json={"type": new_week})


def new_year(now: datetime):
    if now.hour == 0 and now.minute == 0 and now.day == 1 and now.month == 1:
        bot.send_document(CHAT_ID, '/static/files/van.mp3')


def start_cron(event):
    now = datetime.now(tz=timezone('Europe/Kiev'))
    cron = api_request('get', f'crud/cron')[0]
    if cron['run'] == 1:
        for key in cron['jobs']:
            if cron['jobs'][key]['run'] == 1:
                globals()[key](now)
