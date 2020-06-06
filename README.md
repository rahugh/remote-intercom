# Remote Intercom System

This project listens for an intercom to ring, and then sends a notification
with and image of the visitor appearing on the security camera. The notification
contains a link which can be used to activate the intercom and unlock a security
gate.

It is intended to run on a Raspberry Pi using a PiCamera, USB microphone and 5V
servo.

There are two parts, `worker.py` runs in the background listening for a loud ring
and `server.py` runs a Flask webserver which controls the camera, GPIO pins and
sends the notification.


## Install
```
$ pipenv install
```

## Usage

Create an IFTTT webhook notification using these settings and install the IFTTT app on your phone to receive the notification.

- Event name: visitor_arrival
- Link URL: `Value1`
- Image URL: `Value2`

![IFTTT Webhook Settings](https://github.com/rahugh/remote-intercom/raw/master/ifttt_webhook.png)

Copy `.env-dist` to `.env` and change the values to your own or alternatively setup
the environment variables.

You can use `ngrok` to create a public http tunnel to server.py for the
`PUBLIC_HOST` variable.

Run `worker.py` in one screen/tab

```
$ pipenv shell
$ python3 worker.py
```

And run `server.py` in a seperate screen/tab

```
$ pipenv shell
$ python3 server.py
```

Use a loud sound to trigger the notification.
