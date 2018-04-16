from gtts import gTTS
from pydub import AudioSegment
from flask import Flask, request, jsonify, render_template, redirect, send_from_directory
import sys
import os.path

TAGGA_SEGMENTS = 10
tagga_segments = [AudioSegment.from_wav('tagga' + str(i) + '.wav') for i in range(1, TAGGA_SEGMENTS+1)]

app = Flask(__name__)

@app.route('/')
@app.route('/tagga/')
def root():
    return app.send_static_file('index.html')

@app.route('/tagga/api/')
def tagga_form():
    text = request.args.get('text')
    return redirect("/tagga/" + text)

@app.route('/tagga/<string:text>')
def tagga_request(text):
    filename = "static/" + text + ".mp3"

    if not os.path.isfile(filename):
        tagga(text, filename)

    return render_template('tagga.html', searchterm=text)

@app.route('/tagga/static/<path:path>')
def serve_static(path):
    return send_from_directory("static", path)

@app.after_request
def add_cache_control_header(r):
    r.headers['Cache-Control'] = 'no-cache'
    return r

def tagga(text, resultfile):
    tts = gTTS(text=text, lang='sv')
    tts.save('word.mp3')

    word = AudioSegment.from_mp3('word.mp3')

    result = tagga_segments[0] + word
    for tagga_segment in tagga_segments[1:len(tagga_segments)-1]:
        result += tagga_segment + word
    result += tagga_segments[-1]

    result.export(resultfile, format="mp3")

if __name__ == "__main__":
    tagga(sys.argv[1], sys.argv[2])