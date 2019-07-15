import requests
import json
import pytz
import os.path
import random
from datetime import datetime, timedelta
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


def leet_messages(user):
    return ["*" + user + "* kan man 1337a på :sunglasses:",
            "*" + user + "* är 1337e vassare än resten :lennart:",
            "Årets 1337eraturpristagare: *" + user + "* :kungen::medal:",
            "Man skulle kunnna tro att *" + user + "* är från 1337auen :flag-lt:",
            "En 1337er jolt till *" + user + "* :1337_hacker:",
            "1337iumbatterier nånting nånting *" + user + "*",
            "*" + user + "* är riktigt f1337ig :de-e-najs:",
            "*" + user + "* blir aldrig sl1337en :korvsnubbe:",
            "*" + user + "* tillhör e1337en :bogdan_von_knorring:",
            "Alla utom *" + user + "* är 1337erally hitler :hitler::yohitler::sad_hitler::mexihitler::sylt-hitler::adolf_hitler::kanalhitler::analhitler:"]


@app.route("/1337_event", methods=['POST'])
def leet_event():
    event = request.json

    if event["type"] == "url_verification":
        return event["challenge"]
    elif event["type"] == "event_callback":
        inner_event = event["event"]
        event_ts = inner_event["event_ts"]
        event_datetime = ts_to_datetime(event_ts)

        if inner_event.get("subtype") == "message_changed":
            message = inner_event["message"]
            user = name_dic[message["user"]]

            leetcounts, cache_ts = read_cache()
            if message["ts"] == cache_ts:
                post_bot_message("Jag såg")
                post_bot_message("-3 poäng")
                leetcounts[user] -= 3

                write_cache(leetcounts, cache_ts)
                return ""

        if is_1337(event_datetime):
            leetcounts, cache_ts = read_cache()
            cache_datetime = ts_to_datetime(cache_ts)

            user = name_dic[inner_event["user"]]

            if event_datetime.date() > cache_datetime.date():
                post_bot_message(random.choice(leet_messages(user)))

                rand_value = random.random()
                if rand_value < 0.1:
                    post_bot_message("Nänänä, den där går bort i skatt. Alla ska med :lofven:")
                    return ""
                elif 0.1 < rand_value < 0.15:
                    post_bot_message("https://www.youtube.com/watch?v=-08tQxlrYiI")
                    post_bot_message("3 poäng tillbaka på skatten!!")
                    leetcounts[user] += 3
                elif 0.15 < rand_value < 0.25 and is_user_top_5_leeter(user):
                    user_to_recieve_charity = get_user_to_receive_charity()
                    post_bot_message("Dags att ge tillbaks till samhället, fattiga " + user_to_recieve_charity +
                                     " behöver denna leet mer än dig")
                    leetcounts[user_to_recieve_charity] += 1
                else:
                    leetcounts[user] += 1

                if event_datetime.year > cache_datetime.year:
                    post_bot_message("ÅRETS FÖRSTA LEET! 10 bonuspoäng!!! :firework::sparkler::parrot:")
                    leetcounts[user] += 10

                write_cache(leetcounts, event_ts)

            elif event_datetime.date() == cache_datetime.date() and \
                    event_datetime < cache_datetime + timedelta(seconds=3):
                post_bot_message("*" + user + "* suger. -1 poäng :lofven:")
                leetcounts[user] -= 1
                write_cache(leetcounts, event_ts)

    return ""


def is_user_top_5_leeter(user):
    top_leeters = sorted(read_cache()[0].items(), key=itemgetter(1), reverse=True)
    leeter_names_ordered_by_richness = [l[0] for l in top_leeters]
    for i in range(5):
        top_five_leeter = leeter_names_ordered_by_richness[i]
        if user == top_five_leeter:
            return True
    return False


def get_user_to_receive_charity():
    bottom_leeters = sorted(read_cache()[0].items(), key=itemgetter(1), reverse=False)
    leeter_names_ordered_by_poorness = [l[0] for l in bottom_leeters]
    index_of_user_to_get_leet = random.randint(0, 2)
    return leeter_names_ordered_by_poorness[index_of_user_to_get_leet]


def top1337():
    leetcounts = read_cache()[0]

    for name in name_dic.values():
        if name not in leetcounts:
            leetcounts[name] = 0

    return sorted(leetcounts.items(), key=itemgetter(1), reverse=True)
