import os

from deta import Deta
from pymongo import MongoClient

client = MongoClient(os.getenv('MONGO_CONNECTION'))
db = client[os.getenv('DB_NAME')]

app = db.get_collection("apps")
birthday = db.get_collection("birthdays")
lesson = db.get_collection("lessons")
playlist = db.get_collection("playlists")
schedule = db.get_collection("schedules")
teacher = db.get_collection("teachers")
timetable = db.get_collection("timetables")
week = db.get_collection("weeks")
zoom = db.get_collection("zooms")

deta = Deta()
sessions = deta.Base("sessions")
health = deta.Base("health")
