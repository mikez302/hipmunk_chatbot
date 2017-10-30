#!/usr/bin/env python3

import re

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config.from_pyfile('config.py')


class CoordinatesNotFoundError(Exception): pass


def get_coordinates(location_str):
    response = requests.get(
        'https://maps.googleapis.com/maps/api/geocode/json',
        params={'address': location_str, 'key': app.config['GOOGLE_GEOCODING_API_KEY']})
    try:
        location_result = response.json()['results'][0]
    except (IndexError, KeyError) as exc:
        raise CoordinatesNotFoundError from exc
    coords = location_result['geometry']['location']
    return (coords['lat'], coords['lng'])


@app.route('/chat/messages', methods=['POST'])
def handle_message():
    if request.form['action'] == 'message':
        for regex in [r'weather in ([\w\s-]+)', r'([\w\s-]+) weather']:
            matches = re.findall(regex, request.form['text'], re.IGNORECASE)
            if matches:
                location_str = matches[0]
                try:
                    coords = get_coordinates(location_str)
                except CoordinatesNotFoundError:
                    message_text = f'Location “{location_str}” not found.'
                else:
                    message_text = str(coords)
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
