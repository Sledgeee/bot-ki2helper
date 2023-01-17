import json
import db
import cron
from fastapi import FastAPI, Request, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from telebot.types import Update
from deta import App
from bot import bot
from bson import json_util, ObjectId
from responses import UnauthorizedResponse
from security import authorized


app = App(FastAPI())
origins = [
    "http://ki2admin.deta.dev",
    "https://ki2admin.deta.dev"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/col/{collection}")
async def get_collection_json(request: Request, collection: str):
    if authorized(request.headers.get("X-Bot-Auth-Token")) is False:
        return UnauthorizedResponse()

    json_string = json_util.dumps(list(db.db[collection].find()))
    return Response(content=json_string, media_type="application/json")


@app.post("/col/{collection}")
async def post_data(request: Request, collection: str, data: dict):
    if authorized(request.headers.get("X-Bot-Auth-Token")) is False:
        return UnauthorizedResponse()

    result = db.db[collection].insert_one(data).inserted_id
    json_string = json_util.dumps(result)
    return Response(content=json_string, media_type="application/json")


@app.delete("/col/{collection}/{object_id}")
async def delete_data(request: Request, collection: str, object_id: str):
    if authorized(request.headers.get("X-Bot-Auth-Token")) is False:
        return UnauthorizedResponse()

    if len(object_id) < 24:
        return Response(content='{"result": 0, "message": "Incorrect Object Id"}')

    result = {
        "result": db.db[collection].delete_one({"_id": ObjectId(object_id)}).deleted_count
    }
    json_string = json.dumps(result)
    return Response(content=json_string, media_type="application/json")


@app.post("/webhook/bot")
async def webhook(req: Request):
    if req.headers.get('content-type') == 'application/json':
        json_string = await req.json()
        update = Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return status.HTTP_403_FORBIDDEN


@app.lib.run()
@app.lib.cron()
def start_cron(event):
    cron.start_cron(event)


@app.on_event("shutdown")
def shutdown_event():
    db.client.close()
