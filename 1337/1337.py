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

app = Flask(__name__)

def save_top_1337():
    print("Saving toplist to file")

    toplist = get_top_1337();
    with open("1337.json", "w") as toplist_file:
        json.dump(toplist, toplist_file)

scheduler = BackgroundScheduler()
scheduler.add_job(func=save_top_1337, trigger=CronTrigger(hour=13, minute=38))
scheduler.start()

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
        if count != last_count:
            index += 1
        last_count = count

        formatted.append({"index" : index, "name" : name, "count": count})
    return formatted

def get_top_1337():
    tz = pytz.timezone("Europe/Stockholm")

    leetcount = Counter()
    resp = None    
    first_ts = None
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

            unix_ts = float(first_ts.split(".")[0])
            dt = datetime.fromtimestamp(unix_ts, tz)

            if "user" in msg and dt.time().hour == 13 and dt.time().minute == 37 and dt.date() != last_leet_date:
                last_leet_date = dt.date()
                leetcount[name_dic[msg["user"]]] += 1
                
        time.sleep(1)

    return sorted(leetcount.items(), key=itemgetter(1), reverse=True)