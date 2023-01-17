import os
import pytz
import db
from bson import ObjectId
from bot import CHAT_ID, bot
from utils import format_dt
from datetime import datetime


OWNER_ID = os.getenv("OWNER_ID")


def check_birthday(now: datetime):
    if now.hour == 0 and now.minute == 0:
        birthday_items = db.birthday.find({}, {"_id": 0})
        now_formatted = f"{format_dt(now.day)}.{format_dt(now.month)}"
        for item in birthday_items:
            if item['date'] == now_formatted:
                bot.send_message(CHAT_ID, f"{item['student_name']} сьогодні святкує <b>День Народження!</b>",
                                 parse_mode='Html')
                bot.send_sticker(CHAT_ID, "CAACAgIAAxkBAAEG9LhjpKhQ2FUi31gbecql2Kr89xrLBQAChQIAAkGa3Q37oxVj75ZDnywE")


def check_schedule(now: datetime):
    if (now.hour == 7 and now.minute == 55) or 8 < now.hour < 20:
        if db.schedule.count_documents() == 0:
            return
        else:
            week = (db.week.find_one({}, {"_id": 0}))["type"]
            timetable_items = db.timetable.find({}, {"_id": 0}).sort("number")
            schedule_items = db.schedule.find({"day_number": now.weekday() + 1,
                                               "$or": [{"week": week}, {"week": "-"}]}, {"_id": 0}).sort("number")
            for item in schedule_items:
                hour = timetable_items[item["number"] - 1]["start_hour"]
                minute = timetable_items[item["number"] - 1]["start_minute"]
                if minute < 0:
                    hour -= 1
                    minute += 60
                if hour == now.hour and minute == now.minute:
                    lesson = db.lesson.find_one({"_id": item["lesson"]})
                    teacher = db.teacher.find_one({"_id": lesson["teacher"]})
                    zoom = db.zoom.find_one({"lesson": item["lesson"]})
                    return f"⚡️️️⚡️️⚡️ Через 5 хв розпочинається {lesson['type']} {lesson['name']}," \
                           f" {teacher['name']}\nПосилання: {zoom}"


def notify_schedule(now: datetime):
    if now.hour == 7 and now.minute == 30 and now.weekday() < 6:
        pass


def swap_week(now: datetime):
    if now.hour == 0 and now.minute == 0 and now.weekday() == 0:
        week = (db.week.find_one({}, {"_id": 0}))["type"]
        new_week = "Чисельник" if week == "Знаменник" else "Знаменник"
        db.week.update_one({"type": week}, {"$set": {"type": new_week}})
        bot.send_message(OWNER_ID, f"Тиждень оновлено, встановлено {new_week}")


def new_year(now: datetime):
    if now.hour == 0 and now.minute == 0 and now.day == 1 and now.month == 1:
        bot.send_document(CHAT_ID, '/static/files/van.mp3')


def start_cron(event):
    now = datetime.now(tz=pytz.timezone('Europe/Kiev'))
    bot_status = db.health.get("helper")
    if bot_status["status"] == "Online":
        cron = db.app.find_one({"_id": ObjectId(os.getenv("APP_CONFIG_ID"))}, {"_id": 0})['cron']
        jobs = cron['jobs']
        if cron['run']:
            for job in jobs:
                if job['run']:
                    globals()[job['name']](now)
