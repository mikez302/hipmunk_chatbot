#!/usr/bin/env python3

import re

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config.from_pyfile('config.py')


class LocationNotFoundError(Exception): pass

class CoordinatesNotFoundError(Exception): pass

class WeatherNotFoundError(Exception): pass


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


def get_weather(coordinates):
    latitude, longitude = coordinates
    key = app.config['DARK_SKY_API_KEY']
    response = requests.get(f'https://api.darksky.net/forecast/{key}/{latitude},{longitude}')
    weather = response.json()
    try:
        if 'temperature' in weather['currently'] and 'summary' in weather['currently']:
            return weather['currently']
        else:
            raise WeatherNotFoundError()
    except KeyError as exc:
        raise WeatherNotFoundError from exc


@app.route('/chat/messages', methods=['POST'])
def handle_message():
    if request.form['action'] == 'message':
        try:
            location_str = location_from_query(request.form['text'])
            coords = get_coordinates(location_str)
            current_weather = get_weather(coords)
        except LocationNotFoundError:
            message_text = ('I didn\'t understand that. Enter something like ' +
                            '“what\'s the weather in <Location>” or ' +
                            '“weather in <Location>” or “<Location> weather”.')
        except CoordinatesNotFoundError:
            message_text = f'Location “{location_str}” not found.'
        except WeatherNotFoundError:
            message_text = f'Couldn\'t get weather for {location_str}.'
        else:
            temperature = round(current_weather['temperature'])
            summary = current_weather['summary']
            message_text = f'{temperature}°F. {summary}.'
    elif request.form['action'] == 'join':
        message_text = f'Hi {request.form["name"]}'
    else:
        message_text = 'I don\'t know how to handle this situation.'
    response = jsonify(messages=[{'type': 'text', 'text': message_text}])
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
