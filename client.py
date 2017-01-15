#!/usr/bin/env python
from os.path import abspath

import requests
import json
from bson import json_util
import random
from _datetime import datetime
import re

url = 'http://APPURLHERE.rhcloud.com'


def send_outdoor_temp():
    response = requests.get(
            'http://api.openweathermap.org/data/2.5/weather'
            '?q=rataje,pl&units=metric&appid=APIKEYHERE')
    outdoor_temp = response.json()
    send_sensor_temp(datetime.utcnow(), outdoor_temp['main']['temp'], sensor='outdoor')


def send_sensor_temp(date, temp, sensor):
    payload = {'date': date, 'sensor': sensor, 'temp': temp}
    r = requests.post(url, data=json.dumps(payload, default=json_util.default))


def send_temp(date, temp):
    payload = {'date': date, 'sensor': 'room', 'temp': temp}
    r = requests.post(url, data=json.dumps(payload, default=json_util.default))


def send_bulk(payload):
    r = requests.post(url, data=json.dumps(payload, default=json_util.default))


def parse_file(filename):
    f = open(filename, 'r', encoding='utf-8').read().split('\n')
    docs = []
    for line in f[::30]:
        match = re.search("^(?P<date>.*) \| (?P<temp>\d+\.\d+)°C", line)
        if match is not None:
            date = datetime.strptime(match.group("date"), "%a %b %d %H:%M:%S %Y")
            temp = float(match.group("temp"))
            payload = {'date': date, 'sensor': 'room', 'temp': temp}
            docs.append(payload)
    send_bulk(docs)


if __name__ == '__main__':
    exit()
