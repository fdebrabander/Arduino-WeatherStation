#!/usr/bin/env python
import time
import serial
import tornado.ioloop
import tornado.web
import tornado.websocket

from weatherdata import WeatherData

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/index.html")

class WeatherData24H(tornado.web.RequestHandler):
    def get(self):
        self.write({"24h": weather_data.last_day_data()})

class WeatherData7D(tornado.web.RequestHandler):
    def get(self):
        self.write({"7d": weather_data.last_week_data()})

class WeatherWebSocket(tornado.websocket.WebSocketHandler):
    sessions = []

    def open(self):
        self.__class__.sessions.append(self)
        last_hour = weather_data.last_hour_data()
        if len(last_hour):
            self.write_message({"initial": last_hour})

    def on_message(self, message):
        print "Received:", message

    def on_close(self):
        self.__class__.sessions.remove(self)

    @classmethod
    def broadcast(cls, msg):
        for each_session in cls.sessions:
            each_session.write_message(msg)


class SerialReader(object):
    def __init__(self):
        self.readbuf = ""
        self.serial = serial.Serial("/dev/ttyACM0", 9600)
        tornado.ioloop.IOLoop().current().add_handler(self.serial.fileno(),
            self.read_event, tornado.ioloop.IOLoop.READ)

    def parse_readbuf(self):
        while self.readbuf.find("\n") != -1:
            splitted = self.readbuf.split("\n", 1)
            weather_data.new_input(splitted[0])
            if len(splitted) > 1:
                self.readbuf = splitted[1]
            else:
                self.readbuf = ""

    def read_event(self, fd, events):
        self.readbuf += self.serial.read(self.serial.inWaiting())
        self.parse_readbuf()


application = tornado.web.Application([
#    (r"/", IndexHandler),
    (r"/arduino", WeatherWebSocket),
    (r"/weather-24h", WeatherData24H),
    (r"/weather-7d", WeatherData7D),
])

weather_data = WeatherData(WeatherWebSocket)

if __name__ == "__main__":
    serial_reader = SerialReader()
    application.listen(8000)
    tornado.ioloop.IOLoop.instance().start()
