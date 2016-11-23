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

from pyLibrary.debugs.logs import Log
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.thread.threads import Lock, Thread
from pyLibrary.thread.till import Till
from pyLibrary.times.dates import Date
from pyLibrary.times.durations import SECOND


class TestThreads(FuzzyTestCase):
    @classmethod
    def setUpClass(cls):
        Log.start()

    @classmethod
    def tearDownClass(cls):
        Log.stop()

    def test_lock_wait_timeout(self):
        locker = Lock("test")

        def take_lock(please_stop):
            with locker:
                locker.wait(1)
                locker.wait(SECOND)
                locker.wait(till=Date.now()+SECOND)

        Thread.run("take lock", take_lock)

    def test_thread_wait(self):
        NUM = 100
        locker = Lock("test")
        phase1 = []
        phase2 = []

        def work(value, please_stop):
            with locker:
                phase1.append(value)
                locker.wait()
                phase2.append(value)

        with locker:
            threads = [Thread.run(unicode(i), work, i) for i in range(NUM)]

        # CONTINUE TO USE THE locker SO WAITS GET TRIGGERED

        while len(phase2) < NUM:
            with locker:
                pass
        for t in threads:
            t.join()

        self.assertEqual(len(phase1), NUM, "expecting "+unicode(NUM)+" items")
        self.assertEqual(len(phase2), NUM, "expecting "+unicode(NUM)+" items")
        for i in range(NUM):
            self.assertTrue(i in phase1, "expecting "+unicode(i))
            self.assertTrue(i in phase2, "expecting "+unicode(i))
        Log.note("done")

    def test_timeout(self):
        def test(please_stop):
            Thread.sleep(seconds=10)

        now = Date.now()
        thread = Thread.run("sleeper", test)
        Thread.sleep(0.5)
        thread.stop()
        self.assertGreater(now.unix+1, Date.now().unix, "Expecting quick stop")
        Log.note("done")

    def test_sleep(self):
        Thread.sleep(0.5)
        Log.note("done")


    def test_loop(self):
        acc = []
        def worker(please_stop):
            while not please_stop:
                acc.append(Date.now().unix)
                Thread.sleep(0.1)

        Thread.run("loop", worker)
        Thread.sleep(1)

        # We expect 10, but 9 is good enough
        self.assertGreater(len(acc), 9, "Expecting some reasonable number of entries to prove there was looping")

    def test_or_signal_timeout(self):
        acc = []

        def worker(this, please_stop):
            (Till(seconds=0.3) | please_stop).wait_for_go()
            this.assertTrue(not please_stop, "Expecting not to have stopped yet")
            acc.append("worker")

        w = Thread.run("worker", worker, self)
        w.stopped.wait_for_go()
        acc.append("done")

        self.assertEqual(acc, ["worker", "done"])

    def test_or_signal_stop(self):
        acc = []

        def worker(this, please_stop):
            (Till(seconds=0.3) | please_stop).wait_for_go()
            this.assertTrue(not not please_stop, "Expecting to have the stop signal")
            acc.append("worker")

        w = Thread.run("worker", worker, self)
        Till(seconds=0.1).wait_for_go()
        w.stop()
        w.join()
        w.stopped.wait_for_go()
        acc.append("done")

        self.assertEqual(acc, ["worker", "done"])


    def test_and_signals(self):
        acc = []
        locker = Lock()

        def worker(please_stop):
            with locker:
                acc.append("worker")
        a = Thread.run("a", worker)
        b = Thread.run("b", worker)
        c = Thread.run("c", worker)

        (a.stopped & b.stopped & c.stopped).wait_for_go()
        acc.append("done")
        self.assertEqual(acc, ["worker", "worker", "worker", "done"])




