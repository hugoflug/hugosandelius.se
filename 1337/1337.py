import requests
import json
import pytz
import os.path
import random
from datetime import datetime
from operator import itemgetter
from collections import Counter
from flask import Flask, request, render_template, send_from_directory

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
WEB_API_TOKEN = os.environ["SLACK_API_TOKEN"]
CACHE_DIR = os.getenv("CACHE_DIR", ".")
GENERAL_CHANNEL = "C0QJC4S74"

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
    name_dict = {}

    response = requests.get("https://slack.com/api/users.list",
                            params={"token": WEB_API_TOKEN})

    resp = json.loads(response.text)
    for member in resp["members"]:
        name_dict[member["id"]] = member["name"]

    return name_dict


name_dic = get_name_dic()


def format1337(toplist):
    formatted = []
    list_index = 0
    for name, count in toplist:
        list_index += 1

        if count == 0:
            emoji = SCRUB_EMOJI
        else:
            emoji = EMOJIS[list_index - 1] if list_index - 1 < len(EMOJIS) else EMOJIS[-1]
        formatted.append({"name": name, "img": emoji, "count": count})
    return formatted


def ts_to_datetime(ts):
    tz = pytz.timezone("Europe/Stockholm")
    unix_ts = float(ts.split(".")[0])
    return datetime.fromtimestamp(unix_ts, tz)


def is_1337(dt):
    return dt.time().hour == 13 and dt.time().minute == 37


def read_cache():
    with open(CACHE_DIR + "/1337.json", 'r') as cache:
        cache_json = json.load(cache)

    return Counter(cache_json["top"]), cache_json["ts"]


def write_cache(leetcounts, timestamp):
    with open(CACHE_DIR + "/1337.json", 'w') as cache:
        json.dump({
            "ts": timestamp,
            "top": dict(leetcounts)
        }, cache)


if not os.path.isfile(CACHE_DIR + "/1337.json"):
    write_cache({}, "0.0")


def post_bot_message(msg):
    requests.post("https://slack.com/api/chat.postMessage",
                  data={"token": SLACK_BOT_TOKEN,
                        "channel": GENERAL_CHANNEL,
                        "username": "1337bot",
                        "icon_emoji": ":1337_hacker:",
                        "text": msg})


@app.route("/1337_event", methods=['POST'])
def leet_event():
    event = request.json

    if event["type"] == "url_verification":
        return event["challenge"]
    elif event["type"] == "event_callback":
        inner_event = event["event"]
        event_ts = inner_event["event_ts"]
        event_datetime = ts_to_datetime(event_ts)

        if is_1337(event_datetime):
            leetcounts, cache_ts = read_cache()
            cache_datetime = ts_to_datetime(cache_ts)

            if event_datetime.date() > cache_datetime.date():
                if random.random() < 0.1:
                    post_bot_message("Nänänä, den där går bort i skatt. Alla ska med :lofven:")
                    return ""

                user = name_dic[inner_event["user"]]
                leetcounts[user] += 1

                if event_datetime.year > cache_datetime.year:
                    post_bot_message("ÅRETS FÖRSTA LEET! 10 bonuspoäng!!! :firework::sparkler::parrot:")
                    leetcounts[user] += 10

                write_cache(leetcounts, event_ts)

    return ""


def top1337():
    leetcounts = read_cache()[0]

    for name in name_dic.values():
        if name not in leetcounts:
            leetcounts[name] = 0

    return sorted(leetcounts.items(), key=itemgetter(1), reverse=True)
