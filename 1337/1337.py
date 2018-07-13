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


@app.route('/')
@app.route('/1337/')
def index():
    return render_template('index.html', toplist=format1337(top1337()))


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
                            params={"token": WEB_API_TOKEN})

    resp = json.loads(response.text)
    for member in resp["members"]:
        name_dic[member["id"]] = member["name"]

    return name_dic


name_dic = get_name_dic()


def format1337(toplist):
    formatted = []
    index = 0
    last_count = None
    for name, count in toplist:
        index += 1

        if count == 0:
            emoji = SCRUB_EMOJI
        else:
            emoji = EMOJIS[index - 1] if index - 1 < len(EMOJIS) else EMOJIS[-1]
        formatted.append({"name": name, "img": emoji, "count": count})
    return formatted


def ts_to_datetime(ts):
    tz = pytz.timezone("Europe/Stockholm")
    unix_ts = float(ts.split(".")[0])
    return datetime.fromtimestamp(unix_ts, tz)


def is_1337(dt):
    return dt.time().hour == 13 and dt.time().minute == 37


def top1337():
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
    lastleeter = None
    limit_date = ts_to_datetime(limit_ts)

    while not resp or (resp["has_more"] and first_ts > limit_ts):
        response = requests.get("https://slack.com/api/channels.history",
                                params={
                                    "token": WEB_API_TOKEN,
                                    "channel": "C0QJC4S74",
                                    "latest": first_ts
                                })

        resp = json.loads(response.text)
        for msg in resp["messages"]:
            first_ts = msg["ts"]

            if not last_ts:
                last_ts = msg["ts"]

            if first_ts <= limit_ts:
                break

            dt = ts_to_datetime(first_ts)

            if "user" in msg and is_1337(dt) and dt.date() != last_leet_date and limit_date != dt.date():
                lastleeter = msg["user"]

            if (not is_1337(dt)) and lastleeter:
                leetcount[name_dic[lastleeter]] += 1
                lastleeter = None

        time.sleep(1)

    if lastleeter:
        leetcount[name_dic[lastleeter]] += 1
        lastleeter = None

    with open(CACHE_DIR + "/1337.json", "w") as cache:
        cache_data = {
            "ts": last_ts,
            "top": dict(leetcount)
        }
        json.dump(cache_data, cache)

    for name in name_dic.values():
        if name not in leetcount:
            leetcount[name] = 0

    return sorted(leetcount.items(), key=itemgetter(1), reverse=True)
