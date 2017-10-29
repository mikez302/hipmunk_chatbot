#!/usr/bin/env python3

import re

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config.from_pyfile('config.py')


@app.route('/chat/messages', methods=['POST'])
def handle_message():
    if request.form['action'] == 'message':
        for regex in [r'weather in ([\w\s-]+)', r'([\w\s-]+) weather']:
            matches = re.findall(regex, request.form['text'], re.IGNORECASE)
            if matches:
                message_text = matches[0]
                break
        else:  # if location not found
            message_text = ('I didn\'t understand that. Enter something like ' +
                            '“what\'s the weather in <Location>” or ' +
                            '“weather in <Location>” or “<Location> weather”.')
    elif request.form['action'] == 'join':
        message_text = f'Hi {request.form["name"]}'
    else:
        message_text = 'I don\'t know how to handle this situation.'
    response = jsonify(messages=[{'type': 'text', 'text': message_text}])
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
