#!/usr/bin/env python3

import re
from datetime import datetime, timedelta

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
app.config.from_pyfile('config.py')


class LocationNotFoundError(Exception): pass

class CoordinatesNotFoundError(Exception): pass

class WeatherNotFoundError(Exception): pass


def location_from_query(query):
    for regex in [r'weather (?:tomorrow )?in ([\w\s-]+)', r'([\w\s-]+) weather']:
        matches = re.findall(regex, query, re.IGNORECASE)
        if matches:
            return matches[0]
    raise LocationNotFoundError()


def day_from_query(query):
    return 'tomorrow' if 'tomorrow' in query.casefold() else 'today'


def get_location_data(location_str):
    response = requests.get(
        'https://maps.googleapis.com/maps/api/geocode/json',
        params={'address': location_str, 'key': app.config['GOOGLE_GEOCODING_API_KEY']})
    try:
        location_result = response.json()['results'][0]
    except (IndexError, KeyError) as exc:
        raise CoordinatesNotFoundError() from exc
    coords = location_result['geometry']['location']
    return ((coords['lat'], coords['lng']), location_result['formatted_address'])


def get_weather(coordinates, day_str):
    latitude, longitude = coordinates
    key = app.config['DARK_SKY_API_KEY']
    response = requests.get(f'https://api.darksky.net/forecast/{key}/{latitude},{longitude}')
    weather = response.json()
    try:
        if day_str == 'today':
            if 'temperature' in weather['currently'] and 'summary' in weather['currently']:
                return weather['currently']
            else:
                raise WeatherNotFoundError()
        elif day_str == 'tomorrow':
            tomorrow = datetime.today() + timedelta(days=1)
            tomorrow_weather = next(
                (d for d in weather['daily']['data']
                 if datetime.fromtimestamp(d['time']).date() == tomorrow.date()),
                None)
            if tomorrow_weather:
                return tomorrow_weather
            else:
                raise WeatherNotFoundError()
        else:
            raise ValueError('day_str must be \'today\' or \'tomorrow\'')
    except KeyError as exc:
        raise WeatherNotFoundError() from exc


@app.route('/chat/messages', methods=['POST'])
def handle_message():
    if request.form['action'] == 'message':
        try:
            location_str = location_from_query(request.form['text'])
            day_str = day_from_query(request.form['text'])
            coords, formatted_address = get_location_data(location_str)
            weather = get_weather(coords, day_str)
        except LocationNotFoundError:
            message_text = ('I didn\'t understand that. Enter something like ' +
                            '“what\'s the weather in <Location>” or ' +
                            '“weather in <Location>” or “<Location> weather”.')
        except CoordinatesNotFoundError:
            message_text = f'Location “{location_str}” not found.'
        except WeatherNotFoundError:
            message_text = f'Couldn\'t get weather for {formatted_address}.'
        else:
            summary = weather['summary']
            if day_str == 'today':
                temperature = round(weather['temperature'])
                message_text = f'{formatted_address} weather: {temperature}°F. {summary}.'
            elif day_str == 'tomorrow':
                high_temp = round(weather['temperatureMax'])
                low_temp = round(weather['temperatureMin'])
                message_text = (f'{formatted_address} weather for tomorrow: ' +
                                f'high of {high_temp}°F, low of {low_temp}°F. {summary}')
            else:
                message_text = 'Oops, something went wrong'
    elif request.form['action'] == 'join':
        message_text = (f'Hello, {request.form["name"]}! ' +
                        'Ask me about the weather in your city.')
    else:
        message_text = 'I don\'t know how to handle this situation.'
    response = jsonify(messages=[{'type': 'text', 'text': message_text}])
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
