# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
from thread import allocate_lock as _allocate_lock

import requests

from pyLibrary.thread.signal import Signal
from pyLibrary.thread.threads import Thread, ThreadedQueue, MAIN_THREAD

from pyLibrary.collections.queue import Queue
from MoLogs import Log
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.thread.till import Till
from pyLibrary.times.timer import Timer


class TestLocks(FuzzyTestCase):
    @classmethod
    def setUpClass(cls):
        Log.start({"cprofile":True})

    @classmethod
    def tearDownClass(cls):
        Log.stop()

    def test_lock_speed(self):
        SCALE = 1000*100

        with Timer("create"):
            locks = [_allocate_lock() for _ in range(SCALE)]

        with Timer("acquire"):
            for i in range(SCALE):
                locks[i].acquire()

        with Timer("release"):
            for i in range(SCALE):
                locks[i].release()

    def test_queue_speed(self):
        SCALE = 1000*10

        done = Signal("done")
        slow = Queue()
        q = ThreadedQueue("test queue", queue=slow)

        def empty(please_stop):
            while not please_stop:
                item = q.pop()
                if item is Thread.STOP:
                    break

            done.go()

        Thread.run("empty", empty)

        timer = Timer("add {{num}} to queue", param={"num": SCALE})
        with timer:
            for i in range(SCALE):
                q.add(i)
            q.add(Thread.STOP)
            Log.note("Done insert")
            done.wait()

        self.assertLess(timer.duration.seconds, 1.5, "Expecting queue to be fast")


    def test_till_timers(self):

        Till(seconds=1)


        MAIN_THREAD.stop()




def query_activedata(suite, platforms=None):
    query = json.dumps({
        "from": "unittest",
        "limit": 200000,
        "groupby": ["result.test"],
        "select": {"value": "result.duration", "aggregate": "average"},
        "where": {"and": [
            {"eq": {"suite": suite,
                    "build.platform": platforms
                    }},
            {"gt": {"run.timestamp": {"date": "today-week"}}}
        ]},
        "format": "list"
    })

    response = requests.post(
        ACTIVE_DATA_URL,
        data=query,
        stream=True
    )
    response.raise_for_status()
    data = response.json()["data"]
    return data
