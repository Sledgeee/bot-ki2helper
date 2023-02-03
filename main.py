import cron
from fastapi import FastAPI, Request, status
from telebot.types import Update
from deta import App
from bot import bot

app = App(FastAPI())


@app.post("/webhook/bot")
async def webhook(req: Request):
    if req.headers.get('content-type') == 'application/json':
        json_string = await req.json()
        update = Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return status.HTTP_403_FORBIDDEN


@app.post("/ping")
async def ping():
    return "pong"


@app.lib.run()
@app.lib.cron()
def start_cron(event):
    cron.start_cron(event)
