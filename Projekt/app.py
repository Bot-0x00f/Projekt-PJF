import json
import math
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
import colorsys

address = "http://192.168.8.123/json"
CHUNK = 4096
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
        print('message received:  {}'.format(message) )
        global fftThread
        global fftThreadOn
        global numLeds
        global address

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
            with requestsLock:
                state = requests.get(address+"/state")
                turnedOn = state.json()['on']
                requests.post(address, json={'on': not turnedOn})
        elif a == 'state':
            with requestsLock:
                state = requests.get(address).text
            state = '{"cmd": "state",' + state[1:]
            self.write_message(json.loads(state))
            state = json.loads(state)
            numLeds = state["info"]["leds"]["count"]
        elif a == 'bri':
            with requestsLock:
                requests.post(address, json={'bri':int(b)} )
        elif a == 'col':
            with requestsLock:
                requests.post(address, json={"seg":[{"col":[[int(b),int(c),int(d)]]}]} )
        elif a == 'fx':
            with requestsLock:
                requests.post(address, json={"seg":[{"fx":int(b)}]})
        elif a == 'pal':
            with requestsLock:
                requests.post(address, json={"seg": [{"pal": int(b)}]})
        elif a == "lv":
            with requestsLock:
                liveState = requests.get(address+"/json/live").text
            liveState = '{"cmd":"lv",' + liveState[1:]
            self.write_message(json.loads(liveState))
        elif a == "spd":
            with requestsLock:
                requests.post(address, json={"seg":[{"sx":int(b)}]} )
        elif a == "intens":
            with requestsLock:
                requests.post(address, json={"seg":[{"ix":int(b)}]} )
        elif a == "mic":
            if not fftThread.is_alive():
                fftThreadOn = True
                fftThread = threading.Thread(target=fftThreadFunction)
                fftThread.start()
            else:
                fftThreadOn = False
        elif a == "set":        #ustawienia
            if b=="address":    #adres urzadzenia WLED
                settings = open("settings.txt", "tw")
                settings.write("address=http://"+c+"/json\n")
                address = "address=http://"+c+"/json"
                settings.close()
            elif b=="ledsamount":
                with requestsLock:
                    requests.post(address, json={"seg":[{"len": int(c)}]} )


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
    a = np.floor((x - inMin) * (outMax - outMin) / (inMax - inMin) + outMin)
    if a > outMax:
        a = outMax
    elif a < outMin:
        a = outMin
    return a

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
        print("wait")
        time.sleep(0.1)
    sections = [0 for i in range(1, 9)]         #1 sekcja - 1 LED
    secLen = int( (CHUNK/2+1)/numLeds/2 )       # ilosc czestotliwosci na sekcje
    #secLen = 30
    secMax = 0
    RGBData = {"seg":{ "i":[ [0,0,0] for i in range(0,numLeds) ] }}
    while fftThreadOn:
        fftData = np.fft.rfft(VARS['audioData'])
        fftData = np.absolute(fftData)
        fftData = fftData/CHUNK
        for i in range(0, numLeds):
            a = int(secLen*i)
            b = int(secLen*(i+1)-1)
            #print(a,b)
            secMax = max(fftData[int(a):int(b)])
            #print(secMax)
            color = colorsys.hsv_to_rgb(( mapValues(secMax, 0, 10000, 0, 360) + 240)/360, 1, 1)
            r,g,b = color
            #print("Mapowanie ",mapValues(secMax, 0, max(fftData), 0, 360), int(r*255), int(g*255), int(b*255))
            if secMax < 1000:
                r *= secMax/1000
                g *= secMax/1000
                b *= secMax/1000
            RGBData["seg"]["i"][i][0] = int(r*255)
            RGBData["seg"]["i"][i][1] = int(g*255)
            RGBData["seg"]["i"][i][2] = int(b*255)
        with requestsLock:
            requests.post(address, json=RGBData)


fftThread = threading.Thread(target=fftThreadFunction)

application = tornado.web.Application([
    (r'/ws', WSHandler),
    (r'/', MainHandler),
    (r"/svg/(.*)", tornado.web.StaticFileHandler, {"path": "./svg"},),
    (r"/(style\.css)",tornado.web.StaticFileHandler, {"path": "./"},),
    (r"/(script\.js)",tornado.web.StaticFileHandler, {"path": "./"},),
], debug=False )

def getSettings():
    global address
    settings = open("settings.txt", "tr+")
    settings.seek(0, 2)
    if settings.tell() == 0:
        settings.write("address=http://192.168.8.123/json")  # domyslny adres
    settings.seek(0, 0)
    address = settings.readlines()[0]
    address = address.split("=")[1][:-1]
    settings.close()

if __name__ == "__main__":
    getSettings()
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    print('*** Websocket Server Started ***')
    fftThread.start()
    webbrowser.open('http://localhost:8888/')
    tornado.ioloop.IOLoop.instance().start()