import json
import time
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import requests
import webbrowser
import threading
import numpy as np
import pyaudio

address = "http://192.168.8.123/json"
CHUNK = 512
RATE = 44100
INTERVAL = 1
TIMEOUT = 10
pAud = pyaudio.PyAudio()

VARS = {'stream': False,
         'audioData': np.array([])}

numLeds = 9
requestsLock = threading.Lock()
fftThread = None
fftThreadOn = False

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class WSHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        print('new connection')

    def on_message(self, message):
        #print('message received:  {}'.format(message) )
        global fftThread
        global fftThreadOn

        n = message.count(' ')
        if n == 0:
            a = message
        elif n == 1:
            a,b = message.split(" ")
        elif n == 2:
            a,b,c = message.split(" ")
        elif n == 3:
            a,b,c,d = message.split(" ")

        if a == 'onoff':
            with(requestsLock):
                state = requests.get(address+"/state")
                turnedOn = state.json()['on']
                requests.post(address, json={'on': not turnedOn})
        elif a == 'state':
            with(requestsLock):
                state = requests.get(address).text
            state = '{"cmd": "state",' + state[1:]
            self.write_message(json.loads(state))
        elif a == 'bri':
            with(requestsLock):
                requests.post(address, json={'bri':int(b)} )
        elif a == 'col':
            with(requestsLock):
                requests.post(address, json={"seg":[{"col":[[int(b),int(c),int(d)]]}]} )
        elif a == 'fx':
            with(requestsLock):
                requests.post(address, json={"seg":[{"fx":int(b)}]})
        elif a == 'pal':
            with(requestsLock):
                requests.post(address, json={"seg": [{"pal": int(b)}]})
        elif a == "lv":
            with(requestsLock):
                liveState = requests.get(address+"/json/live").text
            liveState = '{"cmd":"lv",' + liveState[1:]
            self.write_message(json.loads(liveState))
        elif a == "mic":
            if not fftThread.is_alive():
                fftThreadOn = True
                fftThread = threading.Thread(target=fftThreadFunction)
                fftThread.start()
            else:
                fftThreadOn = False

    def on_close(self):
        global fftThreadOn
        #tornado.ioloop.IOLoop.instance().stop()
        fftThreadOn = False
        print('connection closed')

    def check_origin(self, origin):
        return True


def callback(in_data, frame_count, time_info, status):
    VARS['audioData'] = np.frombuffer(in_data, dtype=np.int16)
    return (in_data, pyaudio.paContinue)


def mapValues(x, inMin, inMax, outMin, outMax):
    return np.floor((x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin)


def fftThreadFunction():
    global fftThreadOn
    VARS['stream'] = pAud.open(format=pyaudio.paInt16,
                               channels=1,
                               rate=RATE,
                               input=True,
                               frames_per_buffer=CHUNK,
                               stream_callback=callback)

    VARS['stream'].start_stream()
    while VARS['audioData'].size == 0:
        time.sleep(0.1)
    last = 0
    while fftThreadOn:
        fftData = np.fft.rfft(VARS['audioData'])
        fftData = np.absolute(fftData)
        freq = np.fft.rfftfreq(VARS['audioData'].size, d=1. / RATE)
        a, = np.where(fftData == max(fftData))
        a = a[0]
        if last == 0:
            with(requestsLock):
                requests.post(address, json={"seg":[{"col":[[int(0),int(0),int(0)]]}]} )
                requests.post(address, json={"seg": {"i": [int(mapValues(a,0,75,0,8)), [0, 0, 255]]}})
        last = (last + 1) % 10

fftThread = threading.Thread(target=fftThreadFunction)

application = tornado.web.Application([
    (r'/ws', WSHandler),
    (r'/', MainHandler),
    (r"/(style\.css)",tornado.web.StaticFileHandler, {"path": "./"},),
    (r"/(script\.js)",tornado.web.StaticFileHandler, {"path": "./"},),
], debug=False )

if __name__ == "__main__":
    settings = open("settings.txt", "tr+")
    settings.seek(0,2)
    if settings.tell() == 0:
        settings.write("address=http://192.168.8.123/json") #domyslny adres
    settings.seek(0, 0)
    address = settings.readline()
    address = address.split("=")[1]
    settings.close()
    print(address, type(address))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    print('*** Websocket Server Started ***')
    fftThread.start()
    webbrowser.open('http://localhost:8888/')
    tornado.ioloop.IOLoop.instance().start()