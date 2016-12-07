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

from thread import allocate_lock as _allocate_lock

from pyLibrary.thread.signal import Signal
from pyLibrary.thread.threads import Thread, ThreadedQueue

from pyLibrary.collections.queue import Queue
from pyLibrary.debugs.logs import Log
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.times.timer import Timer


class TestLocks(FuzzyTestCase):
    @classmethod
    def setUpClass(cls):
        Log.start({"cprofile":True})

    @classmethod
    def tearDownClass(cls):
        Log.stop()


    def test_lock_speed(self):
        SCALE = 1000*1000

        with Timer("create"):
            locks = [_allocate_lock() for _ in range (SCALE)]

        with Timer("acquire"):
            for i in range(SCALE):
                locks[i].acquire()

        with Timer("release"):
            for i in range(SCALE):
                locks[i].release()

    def test_queue_speed(self):
        SCALE = 1000*100

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

        with Timer("add {{num}} to queue", param={"num":SCALE}):
            for i in range(SCALE):
                q.add(i)
            q.add(Thread.STOP)
            Log.note("Done insert")
            done.wait_for_go()
