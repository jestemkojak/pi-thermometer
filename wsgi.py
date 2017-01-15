#!/usr/bin/env python
import os
import re
import pygal
import json

import requests
from bson import json_util
import logging
from pymongo import MongoClient
from datetime import datetime
from datetime import timedelta

logging.basicConfig(filename='{0}weather.log'.format(os.environ['OPENSHIFT_PYTHON_LOG_DIR']),
                    level=logging.DEBUG,
                    format='%(asctime)s | %(levelname)s | %(message)s')


def application(environ, start_response):
    if environ['REQUEST_METHOD'] == 'POST':
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        request_body = environ['wsgi.input'].read(request_body_size).decode('utf-8')
        logging.debug("BODY: %s", request_body)
        j = json.loads(str(request_body), object_hook=json_util.object_hook)
        # logging.debug("JSON: %s", json.dumps(j))
        save_temp(j)
        save_outdoor_temp()
    ctype = 'text/plain'
    if environ['PATH_INFO'] == '/health':
        response_body = "1"
    if re.search("/(?P<days>[0-9]+)", environ['PATH_INFO']) is not None:
        days = re.search("/(?P<days>[0-9]+)", environ['PATH_INFO']).group("days")
        logging.debug(days)
        chartbase64 = do_chart_with_outdoor(get_temps(days), get_outdoor_temps(days))
        ctype = 'text/html'
        response_body = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
  <title>Temperature chart</title>
</head>
<body>
<img src="''' + chartbase64 + '''"/>
</body>
</html>'''
    else:
        cartbase64 = do_chart(get_temps(1))

        ctype = 'text/html'
        response_body = '''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
  <title>Temperature chart</title>
</head>
<body>
<p>Current temp: ''' + str(get_temp()) + ''' | Outdoor temp: ''' + str(get_outdoor_temp()) + '''</p>
<img src="''' + cartbase64 + '''"/>
</body>
</html>'''
    response_body = response_body.encode('utf-8')

    status = '200 OK'
    response_headers = [('Content-Type', ctype), ('Content-Length', str(len(response_body)))]
    #
    start_response(status, response_headers)
    return [response_body]


def get_mongo():
    mongo_conn_string = os.environ['OPENSHIFT_MONGODB_DB_URL']
    # logging.debug("Connection string: {0}".format(mongo_conn_string))
    client = MongoClient(mongo_conn_string)
    db = client.pogoda
    return db.readings


def save_temp(jsonData):
    readings = get_mongo()
    readings.insert(jsonData)


def save_outdoor_temp():
    response = requests.get(
            'http://api.openweathermap.org/data/2.5/weather'
            '?q=rataje,pl&units=metric&appid=APIKEYHERE')
    outdoor_temp = response.json()
    logging.debug("Weather: {0}".format(json.dumps(outdoor_temp)))
    readings = get_mongo()
    payload = {'date': datetime.utcnow(), 'sensor': 'outdoor', 'temp': outdoor_temp['main']['temp']}
    # jsonData = json.dumps(payload, default=json_util.default)
    readings.insert(payload)


def get_outdoor_temp():
    readings = get_mongo()
    temp = readings.find({"sensor": "outdoor"}).limit(1).sort("date", -1)
    logging.debug("Temp: {0}".format(temp[0]))
    return temp[0]["temp"]


def get_temp():
    readings = get_mongo()
    temp = readings.find({"sensor": "room"}).limit(1).sort("date", -1)
    logging.debug("Temp: {0}".format(temp[0]))
    return temp[0]["temp"]


def get_temps(days):
    if int(days) == 0:
        return get_all_temps()
    else:
        fromdate = datetime.utcnow() - timedelta(days=int(days))
        readings = get_mongo()
        selected = readings.find({"sensor": "room", "date": {"$gte": fromdate}}).sort("date", -1)
        return selected


def get_outdoor_temps(days):
    if int(days) == 0:
        return get_all_outdoor_temps()
    else:
        fromdate = datetime.utcnow() - timedelta(days=int(days))
        readings = get_mongo()
        selected = readings.find({"sensor": "outdoor", "date": {"$gte": fromdate}}).sort("date", -1)
        return selected


def get_all_temps():
    readings = get_mongo()
    alltemps = readings.find({"sensor": "room"}).sort("date", 1)
    logging.debug("Found {0} readings".format(alltemps.count()))
    return alltemps


def get_all_outdoor_temps():
    readings = get_mongo()
    alltemps = readings.find({"sensor": "outdoor"}).sort("date", 1)
    logging.debug("Found {0} outdoor readings".format(alltemps.count()))
    return alltemps


def do_chart(data):
    linechart = pygal.DateTimeLine(
            show_dots=False,
            y_title="Temp [C]",
            x_label_rotation=45,
            truncate_label=-1,
            x_value_formatter=lambda dt: dt.strftime('%d %b %-H:%M'))
    readings = []
    for reading in data:
        readings.append((reading["date"], reading["temp"]))
    linechart.add('room', readings)
    return linechart.render_data_uri()


def do_chart_with_outdoor(data, outdoor_data):
    linechart = pygal.DateTimeLine(
            show_dots=False,
            y_title="Temp [C]",
            x_label_rotation=45,
            truncate_label=-1,
            x_value_formatter=lambda dt: dt.strftime('%d %b %-H:%M'))
    readings = []
    for reading in data:
        readings.append((reading["date"], reading["temp"]))
    linechart.add('room', readings)

    readings = []
    for reading in outdoor_data:
        readings.append((reading["date"], reading["temp"]))
    linechart.add('outdoor', readings)
    return linechart.render_data_uri()


#
# Below for testing only
#
if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    httpd = make_server('localhost', 8051, application)
    # Wait for a single request, serve it and quit.
    httpd.handle_request()
