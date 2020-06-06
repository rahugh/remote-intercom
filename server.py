#!/usr/bin/env python3
#
# This Flask server controls the PiCamera and GPIO pins to take the photo,
# send the notification and unlock the door.
#
# Notifications are triggered by worker.py

import os
import time
import requests
import hashlib
import re
import RPi.GPIO as GPIO
from flask import Flask, request, send_file, g
from picamera import PiCamera

app = Flask(__name__)

notifyPin = 20
unlockPin = 21
servoPin = 17

IMAGE_PATH = '/home/pi/Desktop/'
APP_SECRET = os.environ["APP_SECRET"]
PUBLIC_HOST = os.environ["PUBLIC_HOST"]
IFTTT_KEY = os.environ["IFTTT_KEY"]
LINK_TIMEOUT = 300 # 5 minutes

# regex to check filename for non-alphanumeric characters
isFilename = re.compile('^[\w\d\-]+$')

GPIO.setmode(GPIO.BCM)
GPIO.setup(notifyPin, GPIO.OUT)
GPIO.setup(unlockPin, GPIO.OUT)
GPIO.setup(servoPin, GPIO.OUT)

@app.route("/notify", methods=["GET", "POST"])
def notify():

    # restrict notifications from localhost only
    if request.remote_addr != '127.0.0.1':
        abort(403)

    # LED on
    GPIO.output(notifyPin, GPIO.HIGH)

    # generate a random filename
    filename = time.strftime('%Y%m%d-%H%I%S-') + hashlib.sha1((APP_SECRET + str(os.urandom(32))).encode()).hexdigest()

    # take photo
    camera = PiCamera()
    camera.rotation = 90
    time.sleep(2) # Min 2 seconds to adjust light levels
    camera.capture(IMAGE_PATH + filename + '.jpg')
    camera.close()

    # host the photo
    photo_url = PUBLIC_HOST + '/image/' + filename

    # use filename in one time link
    unlock_url = PUBLIC_HOST + '/unlock/' + filename

    # trigger ifttt notification
    requests.post("https://maker.ifttt.com/trigger/visitor_arrival/with/key/" + IFTTT_KEY, data={
        "value1": unlock_url,
        "value2": photo_url
    })

    # LED off
    GPIO.output(notifyPin, GPIO.LOW)

    return '', 200

# host the image for the rich notification
@app.route("/image/<filename>", methods=["GET"])
def image(filename):

    # check filename is valid and exists
    if isFilename.match(filename) is not None and os.path.exists(IMAGE_PATH + filename + '.jpg'):
        return send_file(IMAGE_PATH + filename + '.jpg', mimetype='image/gif')

    return '<h1>Link expired</h1>', 404

@app.route("/unlock/<filename>", methods=["GET", "POST"])
def unlock(filename):

    # check if link has expired
    path = IMAGE_PATH + filename + '.jpg'
    if isFilename.match(filename) is None or os.path.exists(path) is False or time.time() - os.path.getmtime(path) > LINK_TIMEOUT:
        return '<h1>Link expired</h1>', 404

    # disable link / rename file
    key = hashlib.sha1((APP_SECRET + str(os.urandom(32)) + 'unlock').encode()).hexdigest()
    tofile = filename[:16] + key + '.jpg'
    os.rename(path, IMAGE_PATH + tofile)

    # press button
    # move servo down / LED on
    GPIO.output(unlockPin, GPIO.HIGH)
    g.servo = GPIO.PWM(servoPin, 50)
    g.servo.start(0)
    g.servo.ChangeDutyCycle(7.5)
    time.sleep(1)

    # move servo up / LED off
    GPIO.output(unlockPin, GPIO.LOW)
    g.servo.ChangeDutyCycle(2.5)
    time.sleep(1)
    g.servo.stop()

    return '<h1>Unlocked</h1>', 200

if  __name__ == "__main__":
    try:
        app.run()
    except KeyboardInterrupt:
        print("Closing\n")
    finally:
        GPIO.cleanup()
