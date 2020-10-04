#!/usr/bin/env python
from os import environ

from sanic import Sanic, response
from sanic_compress import Compress
import json
from jinja2 import Template
from camera import VideoCamera
if 'FAKE_ROBOT' not in environ:
    from robot import Robot
else:
    from fake_robot import Robot
from asyncio import sleep
from loguru import logger
import cv2

app = Sanic(__name__)
app.config['COMPRESS_MIMETYPES'] = {'text/html', 'application/json', 'image/jpeg'}
app.config['COMPRESS_LEVEL'] = 9
Compress(app)
app.enable_websocket()

PORT = 5000

cam = VideoCamera()

robot = Robot()

app.static('/index.js', './src/index.js')

with open("res/index.htm", "r") as f:
    index_template = Template(f.read())


@app.route('/')
async def index(request):
    return response.html(index_template.render())


async def frame_generator(resp):
    while True:
        frame = await cam.get_frame()
        blob = b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n'
        await resp.write(blob)


@app.route('/video_feed')
async def video_feed(request):
    return response.stream(frame_generator, content_type='multipart/x-mixed-replace; boundary=frame')


@app.websocket('/ws/command')
async def command_feed(request, ws):
    while True:
        data = await ws.recv()
        if data is None or len(data) == 0:
            continue
        data = json.loads(data)
        left = data['left']
        right = data['right']
        if 'time' in data:
            time = data['time']
            robot.drive(left, right, time)
        else:
            robot.drive(left, right)


@app.websocket('/ws/telemetry')
async def telemetry_feed(request, ws):
    while True:
        info = robot.get_info()
        await ws.send(json.dumps(info))
        await sleep(0.045)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=PORT)