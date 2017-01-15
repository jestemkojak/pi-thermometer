#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, re, time, urllib.request, argparse, client, datetime


def main(argv):
    global readsensor
    global match
    parser = argparse.ArgumentParser(description='Send temperature sensor readings to RPI Sensor server.')
    parser.add_argument("devid", help="your sensor id")
    parser.add_argument("checkfreq", help="temperature check frequency in seconds", type=float)
    parser.add_argument("--logfile", help="logfile path")
    parser.add_argument("--homepage", help="homepage path")
    args = parser.parse_args()

    while 1:
        sensor = open("/sys/bus/w1/devices/%s/w1_slave" % args.devid, "r")
        readsensor = sensor.read()
        sensor.close()
        match = re.search(r'YES\s.*t=(-?[0-9]+)', readsensor, flags=re.IGNORECASE)
        while not match:
            sensor = open("/sys/bus/w1/devices/%s/w1_slave" % args.devid, "r")
            readsensor = sensor.read()
            sensor.close()
            match = re.search(r'YES\s.*t=(-?[0-9]+)', readsensor, flags=re.IGNORECASE)
        readtemp = float(match.group(1)) / 1000
        localtime = time.asctime(time.localtime(time.time()))
        client.send_temp(datetime.datetime.utcnow(), readtemp)
        if args.logfile and not args.logfile.isspace():
            fo = open(args.logfile, "a")
            fo.write("%s | %f°C\n" % (localtime, readtemp))
            fo.close()
        if args.homepage and not args.homepage.isspace():
            fo = open(args.homepage, "w")
            fo.write("<meta http-equiv=""Content-Type"" content=""text/html;charset=utf-8""><body><p>Temperatura: <strong>%f°C</strong></p><p>Czas pomiaru: %s</p></body>" % (readtemp, localtime))
            fo.close()
        time.sleep(args.checkfreq)


if __name__ == "__main__":
    main(sys.argv[1:])


