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
import Adafruit_DHT
import eventlet
import logging
import board
import adafruit_dht
import busio
import adafruit_bmp280


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
eventlet.monkey_patch()
async_mode = None
app = Flask(__name__)
app._static_folder = os.path.abspath("/home/pi/raspboat/static/")
socketio = SocketIO(app, async_mode=async_mode)
thread = None
# gpio.setmode(gpio.BOARD)

# Serial Port
# port = "/dev/ttyAMA0"
port = "/dev/serial0"
ser = serial.Serial(port, baudrate=9600, timeout=0.5)


# Temperature Sensor Type
dhtDevice = adafruit_dht.DHT11(board.D18)

# Pressure Sensor
i2c = busio.I2C(board.SCL, board.SDA)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
bmp280.seaLevelhPa = 1013.25


@app.route("/")
def home():
    global thread
    if thread is None:
        thread = Thread(target=background_stuff)
        thread.start()
    return render_template("index.html")


def read_temperature():
    temperature_c, humidity = None, None
    try:
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity

    except RuntimeError as error:
        pass
    return humidity, temperature_c


def read_pressure():
    press = bmp280.pressure
    alt = bmp280.altitude
    return press, alt
    # print("\nTemperature: %0.1f C" % )
    # print("Pressure: %0.1f hPa" % )
    # print("Altitude = %0.2f meters" % )


def read_gps(lat=0.0, long=0.0, knots=0.0, kmh=0.0):
    data = None
    try:
        data = ser.readline().decode()
    except:
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

    return lat, long, knots, kmh


def background_stuff():
    """ python code in main.py """
    mystr = ""
    print("Starting Thread.")
    lat = 0.0
    long = 0.0
    knots = 0.0
    kmh = 0.0
    temp = 0.0
    press = 0.0
    alt = 0.0
    humid = 0.0
    while True:
        lat, long, knots, kmh = read_gps(lat, long, knots, kmh)
        humid, temp = read_temperature()
        press, alt = read_pressure()

        print((round(press,3), round(alt,3)))

        data_dict = {'data': 'This is data',
                     'lat': round(lat, 3),
                     'long': round(long, 3),
                     'knots': round(knots, 3),
                     'kmh': round(kmh, 3),
                     'humid': round(humid, 3),
                     'temp': round(temp, 3),
                     'press': str(press),
                     'haltitude': alt,
                     }
        socketio.emit('message', data_dict, namespace="/test")
        time.sleep(1)


if __name__ == "__main__":
    socketio.run(app=app, host='0.0.0.0', port=80, debug=False)
