import time

class Average(object):
    """Calculate the average"""
    def __init__(self):
        self._summation = float(0)
        self._count = 0

    def add(self, value):
        self._summation += value
        self._count += 1

    @property
    def average(self):
        if not self._count:
            return 0
        return self._summation / float(self._count)


class RoundedTimer(object):
    """Timer that expires on a clock based minute interval.

    This timer will expire based on the current time. As an example take an the
    rounded time of 15 minutes. If the timer is started when the current time is
    3 minutes past the hour, it will expire at 15 minutes past the hour.
    """
    def __init__(self, round_minutes):
        self._round_sec = round_minutes * 60
        self._start = self._now_minutes()

    def _now_minutes(self):
        return int(time.time()) / self._round_sec * self._round_sec

    def reset(self):
        self._start = self._now_minutes()

    @property
    def time_exceeded(self):
        if self._now_minutes() != self._start:
            return True
        else:
            return False

    @property
    def start_time(self):
        return self._start


if __name__ == "__main__":
    avg = Average()
    minute_timer = RoundedTimer(1)
    count = 1
    while not minute_timer.time_exceeded:
        avg.add(count)
        count += 1
        time.sleep(1)
    print "Start time:", time.ctime(minute_timer.start_time), \
        " average:", avg.average
