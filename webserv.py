#!/usr/bin/env python
import time
import serial
import tornado.ioloop
import tornado.web
import tornado.websocket
import collections

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/index.html")


class WeatherWebSocket(tornado.websocket.WebSocketHandler):
    sessions = []

    def open(self):
        self.__class__.sessions.append(self)
        if len(weather_data.last_hour):
            self.write_message({"initial": list(weather_data.last_hour)})

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


class MinuteAverage(object):
    def __init__(self):
        self._summation = []
        self._count = 0
        self._start = self.now_minutes()

    def now_minutes(self):
        return int(time.time()) / 60 * 60

    def time_exceeded(self):
        if self.now_minutes() != self._start:
            return True
        else:
            return False

    def add_values(self, *values):
        if not len(self._summation):
            self._summation = [float(0) for value in values]
        for index, each_value in enumerate(values):
            self._summation[index] += each_value
        self._count += 1

    @property
    def average(self):
        return [each_summation / float(self._count) for each_summation in self._summation]

    @property
    def start_time(self):
        return self._start


class WeatherData(object):
    def __init__(self):
        self.minute_avg = MinuteAverage()
        self.last_hour = collections.deque()

    def new_input(self, raw_data):
        data = self.parse_data(raw_data)
        if data:
            temperature, pressure = data[0], data[1]
            self.calculate_avg(temperature, pressure)
            WeatherWebSocket.broadcast({
                "temp": temperature,
                "pres": pressure
            })

    def parse_data(self, raw_data):
        values = raw_data.split()
        if len(values) < 2:
            return None
        try:
            return [float(each_item) for each_item in values]
        except:
            return None

    def calculate_avg(self, temperature, pressure):
        if self.minute_avg.time_exceeded():
            temp_avg, pres_avg = self.minute_avg.average 
            self.new_avg(self.minute_avg.start_time, temp_avg, pres_avg)
            self.minute_avg = MinuteAverage()
        else:
            self.minute_avg.add_values(temperature, pressure)

    def new_avg(self, time_seconds, temperature, pressure):
        data = {
            "time": time_seconds * 1000, # Javascript wants miliseconds
            "temp": temperature,
            "pres": pressure
        }
        self.last_hour.append(data)
        if len(self.last_hour) > 60:
            self.last_hour.popleft()
        WeatherWebSocket.broadcast(data)


application = tornado.web.Application([
    (r"/", IndexHandler),
    (r"/arduino", WeatherWebSocket),
])

weather_data = WeatherData()

if __name__ == "__main__":
    serial_reader = SerialReader()
    application.listen(80)
    tornado.ioloop.IOLoop.instance().start()
