import os
import os.path
import urllib.parse
import io
import dlib
import numpy
import requests
import random
import math
import traceback
import json
import re
from threading import Thread
from PIL import Image, ImageDraw
from flask import Flask, request, send_from_directory, send_file

app = Flask(__name__)


def send_response(out_dir, request_url_root, request_text, response_url, username):
    try:
        query, hat_query = request_text.split('/')
        outfilename = query + "_" + hat_query + ".png"

        if not os.path.isfile(out_dir + "/" + outfilename):
            image = hatify(query, hat_query)
            image.save(out_dir + "/" + outfilename)

        img_url = request_url_root + "static/" + urllib.parse.quote(outfilename)

        requests.post(response_url, json={
            'response_type': 'in_channel',
            'text': "Summoned by *" + username + "*\n" + img_url
        })
    except Exception as e:
        traceback.print_exc()
        requests.post(response_url, json={
            'text': "ERROR: " + str(e)
        })


@app.route("/hatify", methods=['POST'])
def hatify_resource():
    request_text = request.form['text']
    response_url = request.form['response_url']
    username = request.form['user_name']

    out_dir = os.environ.get('FILES_DIR', "static")
    thread = Thread(target=send_response, args=(out_dir, request.url_root, request_text, response_url, username))
    thread.start()

    return "Hold on..."


@app.route("/hatify/<string:person>/<string:hat>", methods=['GET'])
def hatify_get(person, hat):
    try:
        image = hatify(person, hat)
        filename = str(random.randint(0, 100000)) + ".png"
        image.save(filename)
        return send_file(filename, mimetype='image/png')
    except Exception as e:
        traceback.print_exc()
        return str(e)


@app.route("/musclify/<string:person>", methods=['GET'])
def musclify_get(person):
    try:
        image = musclify(person)
        filename = str(random.randint(0, 100000)) + ".png"
        image.save(filename)
        return send_file(filename, mimetype='image/png')
    except Exception as e:
        traceback.print_exc()
        return str(e)


def send_musclify_response(out_dir, request_url_root, request_text, response_url, username):
    try:
        outfilename = request_text + str(random.randint(0, 100000)) + ".png"

        image = musclify(request_text)
        image.save(out_dir + "/" + outfilename)

        img_url = request_url_root + "static/" + urllib.parse.quote(outfilename)

        requests.post(response_url, json={
            'response_type': 'in_channel',
            'text': "Summoned by *" + username + "*\n" + img_url
        })
    except Exception as e:
        traceback.print_exc()
        requests.post(response_url, json={
            'text': "ERROR: " + str(e)
        })


@app.route("/musclify", methods=["POST"])
def musclify_resource():
    request_text = request.form['text']
    response_url = request.form['response_url']
    username = request.form['user_name']

    out_dir = os.environ.get('FILES_DIR', "static")

    thread = Thread(target=send_musclify_response,
                    args=(out_dir, request.url_root, request_text, response_url, username))
    thread.start()

    return "Hold on..."


@app.route('/static/<path:path>')
def serve_static(path):
    static_dir = os.environ.get('FILES_DIR', "static")
    return send_from_directory(static_dir, path)


detect_faces = dlib.get_frontal_face_detector()
predict_face_shape = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")


def get_face_shape(image):
    img = numpy.array(image.convert('L'))
    faces = detect_faces(img)

    if len(faces) == 0:
        return None

    shape = predict_face_shape(img, faces[0])
    pointlist = [(point.x, point.y) for point in shape.parts()]

    return pointlist[17:26] + list(reversed(pointlist[0:17]))


def find_bbox(points):
    x_min = min(p[0] for p in points)
    x_max = max(p[0] for p in points)
    y_min = min(p[1] for p in points)
    y_max = max(p[1] for p in points)

    return x_min, y_min, x_max, y_max


def crop_polygon(image, points):
    im_array = numpy.asarray(image)

    mask_im = Image.new('L', (im_array.shape[1], im_array.shape[0]), 0)
    ImageDraw.Draw(mask_im).polygon(points, outline=1, fill=1)
    mask = numpy.array(mask_im)

    new_im_array = numpy.empty(im_array.shape, dtype='uint8')
    new_im_array[:, :, :3] = im_array[:, :, :3]
    new_im_array[:, :, 3] = mask * 255

    return Image.fromarray(new_im_array, "RGBA")


def find_face(image):
    face_shape = get_face_shape(image)

    if not face_shape:
        return None

    new_image = crop_polygon(image, face_shape)
    return new_image.crop(find_bbox(face_shape))


def enhance(image):
    maxval = 0
    minval = 9999
    for pixel in image.getdata():
        r, g, b, a = pixel
        if a == 255:
            if r > maxval:
                maxval = r
            if g > maxval:
                maxval = g
            if b > maxval:
                maxval = b
            if r < minval:
                minval = r
            if g < minval:
                minval = g
            if b < minval:
                minval = b
    interval = maxval - minval
    mul = 255.0 / interval

    source = image.split()
    r, g, b = 0, 1, 2

    source[r].paste(source[r].point(lambda x: min(255, int((x - minval) * mul))))
    source[g].paste(source[g].point(lambda x: min(255, int((x - minval) * mul))))
    source[b].paste(source[b].point(lambda x: min(255, int((x - minval) * mul))))

    return Image.merge(image.mode, source)


SEARCH_ENGINE_URL = "https://www.googleapis.com/customsearch/v1"
SEARCH_API_KEY = os.environ["SEARCH_API_KEY"]
SEARCH_API_ENGINE_ID = os.environ["SEARCH_API_ENGINE_ID"]
SLACK_API_EMOJIFY_TOKEN = os.environ["SLACK_API_EMOJIFY_TOKEN"]
CHROME_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) " \
                    "Chrome/41.0.2227.1 Safari/537.36"


def search_image(query, start_index=0):
    response = requests.get(SEARCH_ENGINE_URL,
                            params={"searchType": "image",
                                    "cx": SEARCH_API_ENGINE_ID,
                                    "key": SEARCH_API_KEY,
                                    "q": query})

    if response.status_code != 200:
        if response.status_code == 429:
            raise Exception("Rate limit reached on search API!")
        else:
            raise Exception("Could not perform search, HTTP error from search API: " + str(response.status_code))

    obj = json.loads(response.text)

    results = obj["items"]
    for result in results[start_index:]:
        img_url = result["link"]
        try:
            img_response = requests.get(img_url, verify=False, headers={'User-Agent': CHROME_USER_AGENT})
        except ConnectionError:
            continue

        if img_response.status_code == 200:
            yield Image.open(io.BytesIO(img_response.content)).convert("RGBA")


def within_range(value, reference, _range):
    return reference - _range < value < reference + _range


COLOR_DIFF_RANGE = 15


def make_bg_transparent_and_crop(image):
    pixdata = image.load()

    bg_color = pixdata[0, 0]

    width, height = image.size
    max_x = 0
    max_y = 0
    min_x = width
    min_y = height

    for y in range(height):
        for x in range(width):
            pixel = pixdata[x, y]

            if all(within_range(pixel[i], bg_color[i], COLOR_DIFF_RANGE) for i in range(0, 4)):
                pixdata[x, y] = (255, 255, 255, 0)
            else:
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y

    return image.crop((min_x, min_y, max_x, max_y))


def get_hat(query):
    hat = next(search_image(query), None)

    if not hat:
        return None

    return make_bg_transparent_and_crop(hat)


def find_bottom_nontransparent_pos(image):
    pixdata = image.load()

    bottompositions = []

    width, height = image.size
    for y in range(height):
        for x in range(width):
            pixel = pixdata[x, y]
            if pixel[3] != 0:
                if len(bottompositions) == 0 or y == bottompositions[0][1]:
                    bottompositions.append((x, y))
                elif y > bottompositions[0][1]:
                    bottompositions.clear()
                    bottompositions.append((x, y))

    if len(bottompositions) == 0:
        return int(width / 2), height - 1

    return bottompositions[int(len(bottompositions) / 2) + 1]


LEFT_EYEBROW_RIGHT_END = 4
RIGHT_EYEBROW_LEFT_END = 5


def add_hat(image, original_image, hat_image):
    face_shape = get_face_shape(original_image)
    bbox = find_bbox(face_shape)

    x_offset = bbox[0]
    y_offset = bbox[1]

    lere = (face_shape[LEFT_EYEBROW_RIGHT_END][0] - x_offset, face_shape[LEFT_EYEBROW_RIGHT_END][1] - y_offset)
    rele = (face_shape[RIGHT_EYEBROW_LEFT_END][0] - x_offset, face_shape[RIGHT_EYEBROW_LEFT_END][1] - y_offset)
    hatpos_x = int((lere[0] + rele[0]) / 2)
    hatpos_y = int((lere[1] + rele[1]) / 2) + int(hat_image.height / 20)

    bottom = find_bottom_nontransparent_pos(hat_image)

    new_image = Image.new(image.mode, (image.width * 2, image.height * 2))
    new_image.paste(image, (int(image.width / 2), image.height))
    new_image.paste(hat_image, (int(image.width / 2) + hatpos_x - bottom[0], image.height + hatpos_y - bottom[1]),
                    hat_image)

    return new_image


def find_nontransparent_bbox(image):
    pixdata = image.load()

    width, height = image.size
    min_x = width
    max_x = 0

    min_y = height
    max_y = 0

    for y in range(height):
        for x in range(width):
            pixel = pixdata[x, y]

            if pixel[3] != 0:
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y

    return min_x, min_y, max_x, max_y


def hatify(query, hat_query):
    face = None
    for image in search_image(query):
        face = find_face(image)
        if face:
            break

    if not face:
        raise Exception("No face found for " + query)

    hat = get_hat(hat_query)

    if not hat:
        raise Exception("No hat found for " + hat_query)

    hat.thumbnail((face.width, face.height))

    combined = add_hat(face, image, hat)

    img_bbox = find_nontransparent_bbox(combined)
    # combined.thumbnail((128, 128))
    return combined.crop(img_bbox)


def get_random_image(query):
    yield from search_image(query, start_index=random.randint(0, 20))


def get_rotation(face_shape):
    xre = face_shape[RIGHT_EDGE][0]
    yre = face_shape[RIGHT_EDGE][1]
    xle = face_shape[LEFT_EDGE][0]
    yle = face_shape[LEFT_EDGE][1]

    return math.degrees(math.atan2(yle - yre, xre - xle))


RIGHT_EDGE = 10
LEFT_EDGE = -1
CHIN_BOTTOM = -8


def musclify(query, guy_query="muscle guy"):
    for muscles in get_random_image(guy_query):
        muscles_face_shape = get_face_shape(muscles)
        if muscles_face_shape:
            break

    muscles_bbox = find_bbox(muscles_face_shape)

    for image in search_image(query):
        og_face_shape = get_face_shape(image)
        if not og_face_shape:
            continue
        face_image = crop_polygon(image, og_face_shape)
        face_image = face_image.crop(find_bbox(og_face_shape))

        face_image = face_image.resize((muscles_bbox[2] - muscles_bbox[0], muscles_bbox[3] - muscles_bbox[1]))
        face_shape = get_face_shape(face_image)
        if face_shape:
            break

    if not face_shape:
        raise Exception("No face found for " + query)

    rot_face_image = face_image.rotate(get_rotation(muscles_face_shape) - get_rotation(face_shape),
                                       resample=Image.BILINEAR)
    rot_face_shape = get_face_shape(face_image)

    if rot_face_shape:
        face_image = rot_face_image
        face_shape = rot_face_shape

    muscles.paste(face_image, (muscles_face_shape[CHIN_BOTTOM][0] - face_shape[CHIN_BOTTOM][0],
                               muscles_face_shape[CHIN_BOTTOM][1] - face_shape[CHIN_BOTTOM][1]), face_image)
    return muscles


@app.route("/emojify_msg", methods=['POST'])
def emojify_msg():
    event = request.json

    if event["type"] == "url_verification":
        return event["challenge"]
    elif event["type"] == "event_callback":
        inner_event = event["event"]

        existing_emojis = get_emoji_list()

        emojis = re.findall(":[^ ]+:", inner_event["text"])
        for emoji in emojis:
            if emoji not in existing_emojis:
                emojify(emoji, emoji)

    return ""


@app.route("/emojify", methods=['POST'])
def emojify_resource():
    request_text = request.form['text']
    response_url = request.form['response_url']
    username = request.form['user_name']

    thread = Thread(target=send_emojify_response, args=(request_text, response_url, username))
    thread.start()

    return "Hold on..."


def send_emojify_response(request_text, response_url, username):
    try:
        emoji_name = request_text.replace(" ", "_")

        emojify(request_text, emoji_name)

        requests.post(response_url, json={
            'response_type': 'in_channel',
            'text': "Requested by *" + username + "*\n" + ":" + emoji_name + ":"
        })
    except Exception as e:
        traceback.print_exc()
        requests.post(response_url, json={
            'text': "ERROR: " + str(e)
        })


def emojify(query, emoji_name):
    for image in search_image(query):
        face = find_face(image)
        if face:
            face.save("tmp.png")
            upload_emoji(open("tmp.png", "rb"), emoji_name)
            return

    raise Exception("No face found for: " + query)


def upload_emoji(file, emoji_name):
    response = requests.post("https://slack.com/api/emoji.add",
                             data={
                                 'token': SLACK_API_EMOJIFY_TOKEN,
                                 'mode': 'data',
                                 'name': emoji_name,
                             }, files={
                                 "image": file
                             })

    resp = json.loads(response.text)

    if "error" in resp:
        raise Exception("Could not upload emoji: " + resp["error"])


def get_emoji_list():
    response = requests.get("https://slack.com/api/emoji.list", params={"token": SLACK_API_EMOJIFY_TOKEN})
    resp = json.loads(response.text)
    return resp["emoji"]
