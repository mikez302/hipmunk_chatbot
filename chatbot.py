#!/usr/bin/env python3

import re

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config.from_pyfile('config.py')


class LocationNotFoundError(Exception): pass

class CoordinatesNotFoundError(Exception): pass


def location_from_query(query):
    for regex in [r'weather in ([\w\s-]+)', r'([\w\s-]+) weather']:
        matches = re.findall(regex, query, re.IGNORECASE)
        if matches:
            return matches[0]
    raise LocationNotFoundError()


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
        try:
            location_str = location_from_query(request.form['text'])
            coords = get_coordinates(location_str)
        except LocationNotFoundError:
            message_text = ('I didn\'t understand that. Enter something like ' +
                            '“what\'s the weather in <Location>” or ' +
                            '“weather in <Location>” or “<Location> weather”.')
        except CoordinatesNotFoundError:
            message_text = f'Location “{location_str}” not found.'
        else:
            message_text = str(coords)
    elif request.form['action'] == 'join':
        message_text = f'Hi {request.form["name"]}'
    else:
        message_text = 'I don\'t know how to handle this situation.'
    response = jsonify(messages=[{'type': 'text', 'text': message_text}])
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
