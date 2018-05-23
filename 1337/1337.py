import requests
import json
import pytz
import time
import os.path
import os
from datetime import datetime
from collections import Counter
from operator import itemgetter
from flask import Flask, request, jsonify, render_template

WEB_API_TOKEN = os.environ["TOKEN"]
CACHE_DIR = os.getenv("CACHE_DIR", ".")

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html', toplist=top1337())

def get_name_dic():
    name_dic = {}

    response = requests.get("https://slack.com/api/users.list", 
        params={"token" : WEB_API_TOKEN})

    resp = json.loads(response.text)
    for member in resp["members"]:
        name_dic[member["id"]] = member["name"]

    return name_dic

name_dic = get_name_dic()

def top1337():
    tz = pytz.timezone("Europe/Stockholm")

    try:
        with open(CACHE_DIR + "/1337.json") as cache:
            cache_json = json.load(cache)
            leetcount = Counter(cache_json["top"])
            limit_ts = cache_json["ts"]
    except IOError:
        leetcount = Counter()
        limit_ts = "0"

    resp = None    
    first_ts = None
    last_ts = None
    last_leet_date = None

    while not resp or (resp["has_more"] and first_ts > limit_ts):
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
                last_ts = first_ts

            if first_ts <= limit_ts:
                break

            unix_ts = float(first_ts.split(".")[0])
            dt = datetime.fromtimestamp(unix_ts, tz)

            if "user" in msg and dt.time().hour == 13 and dt.time().minute == 37 and dt.date() != last_leet_date:
                last_leet_date = dt.date()
                leetcount[name_dic[msg["user"]]] += 1

        time.sleep(1)

    with open(CACHE_DIR + "/1337.json", "w") as cache:
        cache_data = {
            "ts" : last_ts,
            "top" : dict(leetcount)    
        }
        json.dump(cache_data, cache)

    return sorted(leetcount.items(), key=itemgetter(1), reverse=True)