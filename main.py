from flask import Flask, render_template
from flask_socketio import SocketIO
import datetime
import time
import os
from threading import Thread
import serial
import string
import pynmea2
import RPi.GPIO as gpio
import eventlet
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
eventlet.monkey_patch()
async_mode = None
app = Flask(__name__)
app._static_folder = os.path.abspath("/home/pi/mocapi/static/")
socketio = SocketIO(app, async_mode=async_mode)
thread = None
# port = "/dev/ttyAMA0"
port = "/dev/serial0"
ser = serial.Serial(port, baudrate=9600, timeout=0.5)


@app.route("/")
def home():
    global thread
    if thread is None:
        thread = Thread(target=background_stuff)
        thread.start()
    return render_template("index.html")


def background_stuff():
    """ python code in main.py """
    mystr = ""
    data = None
    lat = 0.0
    long = 0.0
    knots = 0.0
    kmh = 0.0
    print("Starting Thread.")
    while True:
        try:
            data = ser.readline().decode()
        except:
            #print("   \tloading\t   ", end="\r")
            pass
        if data and data[0:6] == '$GPRMC':
            try:
                msg = pynmea2.parse(data)
                lat = msg.latitude
                long = msg.longitude
            except:
                pass
            speed = float(data.split(",")[7])
            knots = speed
            kmh = speed * 1.852
            mystr = "Latitude: {:.2f}\tLongitude: {:.2f}\tSpeed (Knots): {:.2f}\tSpeed (Km/h): {:.2f}".format(
                lat, long, speed, speed * 1.852)
            #print(mystr, end="\r")
            time.sleep(0.5)

        data_dict = {'data': 'This is data',
                     'lat': round(lat, 3),
                     'long': round(long, 3),
                     'knots': round(knots, 3),
                     'kmh': round(kmh, 3)}
        socketio.emit('message', data_dict, namespace="/test")
        # time.sleep(0.5)


if __name__ == "__main__":
    socketio.run(app=app, host='0.0.0.0', port=80, debug=False)
