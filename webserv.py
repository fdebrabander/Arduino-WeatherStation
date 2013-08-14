#!/usr/bin/env python
import serial
import tornado.ioloop
import tornado.web
import tornado.websocket

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("static/index.html")

class ArduinoData(tornado.websocket.WebSocketHandler):
    sessions = []

    def open(self):
        self.write_message("WebSocket open!")
        ArduinoData.sessions.append(self)

    def on_message(self, message):
        print "Received:", message

    def on_close(self):
        ArduinoData.sessions.remove(self)

class SerialReader(object):
    def __init__(self):
        self.readbuf = ""
        self.serial = serial.Serial("/dev/ttyACM0", 9600)
        tornado.ioloop.IOLoop().current().add_handler(self.serial.fileno(),
            self.read_event, tornado.ioloop.IOLoop.READ)

    def parse_readbuf(self):
        while self.readbuf.find("\n") != -1:
            splitted = self.readbuf.split("\n", 1)
            for each_session in ArduinoData.sessions:
                each_session.write_message(splitted[0])
            if len(splitted) > 1:
                self.readbuf = splitted[1]
            else:
                self.readbuf = ""

    def read_event(self, fd, events):
        self.readbuf += self.serial.read(self.serial.inWaiting())
        self.parse_readbuf()

application = tornado.web.Application([
    (r"/", IndexHandler),
    (r"/arduino", ArduinoData),
])

if __name__ == "__main__":
    serial_reader = SerialReader()
    application.listen(80)
    tornado.ioloop.IOLoop.instance().start()
