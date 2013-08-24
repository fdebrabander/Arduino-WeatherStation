import json
import redis

from average import Average, RoundedTimer
from sample import Sample

class WeatherData(object):
    def __init__(self, websock):
        self.websock = websock
        self.minute_timer = RoundedTimer(1)
        self.quarter_timer = RoundedTimer(15)
        self.hour_timer = RoundedTimer(60)
        self.minute_avg = Sample(Average(), Average())
        self.quarter_avg = Sample(Average(), Average())
        self.hour_avg = Sample(Average(), Average())
        self.redis = redis.StrictRedis(host="localhost")

    def new_input(self, raw_data):
        data = self.parse_data(raw_data)
        if data:
            temperature, pressure = data[0], data[1]
            self.calculate_avg(temperature, pressure)
            self.websock.broadcast({
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
        self.update_average(
            temperature, pressure, self.minute_timer, self.minute_avg, self.new_minute_avg
        )

    def new_minute_avg(self, start_time, temperature, pressure):
        self.update_average(
            temperature, pressure, self.quarter_timer, self.quarter_avg, self.store_quarter_avg
        )
        self.update_average(
            temperature, pressure, self.hour_timer, self.hour_avg, self.store_hour_avg
        )
        data = self.avg_to_dict(start_time, temperature, pressure)
        self.websock.broadcast(data)
        self.store_minute_avg(data)

    def update_average(self, temperature, pressure, timer, average, time_exceeded_handler):
        if timer.time_exceeded:
            time_exceeded_handler(
                timer.start_time,
                average.temperature.average,
                average.pressure.average
            )
            timer.reset()
            average = Sample(Average(), Average())
        average.temperature.add(temperature)
        average.pressure.add(pressure)

    def avg_to_dict(self, time_seconds, temperature, pressure):
        return {
            "time": time_seconds * 1000, # Javascript wants miliseconds
            "temp": temperature,
            "pres": pressure
        }

    def store_quarter_avg(self, time, temperature, pressure):
        data = self.avg_to_dict(time, temperature, pressure)
        self.redis.lpush("quarter_avg", json.dumps(data, separators=(',', ':')))
        self.redis.ltrim("quarter_avg", 0, 15 * 4 * 24 - 1)  # Store 15min avg. for 24 hours

    def store_hour_avg(self, time, temperature, pressure):
        data = self.avg_to_dict(time, temperature, pressure)
        self.redis.lpush("hour_avg", json.dumps(data, separators=(',', ':')))
        self.redis.ltrim("hour_avg", 0, 24 * 365 - 1)  # Store 1h avg. for 365 days

    def store_minute_avg(self, data):
        self.redis.lpush("minute_avg", json.dumps(data, separators=(',', ':')))
        self.redis.ltrim("minute_avg", 0, 59)

    def unserialize_redis_data(self, data):
        return [json.loads(item) for item in data]

    def last_hour_data(self):
        data = self.redis.lrange("minute_avg", 0, -1)
        return self.unserialize_redis_data(data)

    def last_day_data(self):
        data = self.redis.lrange("quarter_avg", 0, -1)
        return self.unserialize_redis_data(data)

    def last_week_data(self):
        data = self.redis.lrange("hour_avg", 0, 24 * 7 - 1)
        return self.unserialize_redis_data(data)
