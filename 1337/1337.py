import requests
import json
import pytz
import time
import os.path
import os
from datetime import datetime
from collections import Counter
from operator import itemgetter
from flask import Flask, request, jsonify, render_template, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

WEB_API_TOKEN = os.environ["SLACK_API_TOKEN"]
CACHE_DIR = os.getenv("CACHE_DIR", ".")

EMOJIS = [
    "https://emoji.slack-edge.com/T0QJDQ4MC/hackerman-matrix/79021d6f4a7c07e4.gif",
    "https://emoji.slack-edge.com/T0QJDQ4MC/hackerman_triggered/b1951faae08e5b77.gif",
    "https://emoji.slack-edge.com/T0QJDQ4MC/hackerman/bd0c31e800d5de3f.png",
    "https://emoji.slack-edge.com/T0QJDQ4MC/neckbeard_borgen/c9b3bdce923311ab.png",
    "https://emoji.slack-edge.com/T0QJDQ4MC/neckbeard/c8ec7bf188.png"
]

SCRUB_EMOJI = "https://emoji.slack-edge.com/T0QJDQ4MC/sylten/d99fe0d901f540a2.jpg"

app = Flask(__name__)

def save_top_1337():
    print("Saving toplist to file")

    toplist = get_top_1337();
    with open("1337.json", "w") as toplist_file:
        json.dump(toplist, toplist_file)

@app.route('/')
@app.route('/1337/')
def index():
    with open("1337.json") as toplist_file:
        toplist = json.load(toplist_file)
        return render_template('index.html', toplist=format_toplist(toplist))

@app.route('/1337/static/<path:path>')
def serve_static(path):
    return send_from_directory("static", path)

@app.after_request
def add_cache_control_header(r):
    r.headers['Cache-Control'] = 'no-cache'
    return r

def get_name_dic():
    name_dic = {}

    response = requests.get("https://slack.com/api/users.list", 
        params={"token" : WEB_API_TOKEN})

    resp = json.loads(response.text)
    for member in resp["members"]:
        name_dic[member["id"]] = member["name"]

    return name_dic

name_dic = get_name_dic()

def format_toplist(toplist):
    formatted = []
    index = 0
    last_count = None
    for name, count in toplist:
        index += 1

        last_count = count

        emoji = EMOJIS[index - 1] if index - 1 < len(EMOJIS) else SCRUB_EMOJI
        formatted.append({"name" : name, "img" : emoji, "count" : count})
    return formatted

def get_top_1337():
    tz = pytz.timezone("Europe/Stockholm")

    leetcount = Counter()
    resp = None    
    first_ts = None
    last_ts = None
    last_leet_date = None

    while not resp or resp["has_more"]:
        response = requests.get("https://slack.com/api/channels.history", 
            params={
                "token" : WEB_API_TOKEN,
                "channel" : "C0QJC4S74",
                "latest" : first_ts
            })

        resp = json.loads(response.text)
        for msg in resp["messages"]:
            first_ts = msg["ts"]

            if not last_ts:
                last_ts = msg["ts"]

            unix_ts = float(first_ts.split(".")[0])
            dt = datetime.fromtimestamp(unix_ts, tz)

            if "user" in msg and dt.time().hour == 13 and dt.time().minute == 37 and dt.date() != last_leet_date:
                last_leet_date = dt.date()
                leetcount[name_dic[msg["user"]]] += 1
                
        time.sleep(1)

    for name in name_dic.values():
        if name not in leetcount:
            leetcount[name] = 0 

    #with open("timestamp", "w") as tsfile:
    #    tsfile.write(str(last_ts))

    return sorted(leetcount.items(), key=itemgetter(1), reverse=True)


if not os.path.isfile("1337.json"):
    save_top_1337()

scheduler = BackgroundScheduler()
scheduler.add_job(func=save_top_1337, trigger=CronTrigger(hour=13, minute=38))
scheduler.start()