#!/usr/bin/env python3
# This program continuously listens for a sound that meets the VOLUME_THRESHOLD
# then triggers a web request to server.py
#
# Based on: https://stackoverflow.com/questions/1936828/how-get-sound-input-from-microphone-in-python-and-process-it-on-the-fly

import alsaaudio
import time
import audioop
import requests

VOLUME_THRESHOLD = 40
RINGING_TIME = 10
NOTIFY_HOST = 'http://127.0.0.1:5000'

# Wait for intercom to ring
def main():

    # Open the device in nonblocking capture mode. The last argument could
    # just as well have been zero for blocking mode. Then we could have
    # left out the sleep call in the bottom of the loop
    inp = alsaaudio.PCM(alsaaudio.PCM_CAPTURE, alsaaudio.PCM_NONBLOCK)

    # Set attributes: Mono, 8000 Hz, 16 bit little endian samples
    inp.setchannels(1)
    inp.setrate(8000)
    inp.setformat(alsaaudio.PCM_FORMAT_S16_LE)

    # The period size controls the internal number of frames per period.
    # The significance of this parameter is documented in the ALSA api.
    # For our purposes, it is suficcient to know that reads from the device
    # will return this many frames. Each frame being 2 bytes long.
    # This means that the reads below will return either 320 bytes of data
    # or 0 bytes of data. The latter is possible because we are in nonblocking
    # mode.
    inp.setperiodsize(160)

    ringing = 0
    notified = False

    # pause here for the mic to calm down
    time.sleep(2)

    print("Listening...")
    while True:
        try:
            # Read data from device
            l, data = inp.read()
            if l:
                print(audioop.max(data, 2), end="\r")
                # Check the maximum of the absolute value of all samples in a fragment.
                if audioop.max(data, 2) > VOLUME_THRESHOLD:
                    ringing += 1 if ringing < RINGING_TIME else 0
                else:
                    ringing -= 1 if ringing > 0 else 0

            if ringing >= RINGING_TIME and notified == False:
                notified = True
                notify()

            # reset once quiet
            elif ringing == 0 and notified == True:
                print("Reset")
                notified = False

            time.sleep(.001)
        except:
            pass


def notify():
    print("Sending notification")

    # trigger web app to send notification
    requests.post(NOTIFY_HOST + "/notify")

#
# main()
#
if __name__ == "__main__":
    main()
