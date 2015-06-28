# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import unicode_literals
from pyLibrary.meta import cache
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.thread.threads import Thread
from pyLibrary.times.durations import SECOND


CACHE_DURATION = 5 * SECOND

call_count = 0


class TestCNV(FuzzyTestCase):
    def test_forever_cache(self):
        global call_count
        call_count = 0

        self.assertEqual(forever_func(), 42)
        self.assertEqual(forever_func(), 42)
        self.assertEqual(forever_func(), 42)
        self.assertEqual(forever_func(), 42)
        self.assertEqual(call_count, 0)

        Thread.sleep(seconds=CACHE_DURATION.seconds)

        self.assertEqual(forever_func(), 42)
        self.assertEqual(forever_func(), 42)
        self.assertEqual(forever_func(), 42)
        self.assertEqual(forever_func(), 42)
        self.assertEqual(call_count, 0)


    def test_forever_cache_many(self):
        global call_count
        call_count = 0

        for i in range(10000):
            self.assertEqual(forever_func(), 42)
        self.assertEqual(call_count, 0)



    def test_single_cache(self):
        global call_count
        call_count = 0

        self.assertEqual(single_func(), 42)
        self.assertEqual(single_func(), 42)
        self.assertEqual(single_func(), 42)
        self.assertEqual(single_func(), 42)
        self.assertEqual(call_count, 1)

        Thread.sleep(seconds=CACHE_DURATION.seconds)

        self.assertEqual(single_func(), 42)
        self.assertEqual(single_func(), 42)
        self.assertEqual(single_func(), 42)
        self.assertEqual(single_func(), 42)
        self.assertEqual(call_count, 2)


    def test_self_cache(self):
        global call_count
        call_count = 0

        obj = MyType()

        self.assertEqual(obj.method0(), 2)
        self.assertEqual(obj.method0(), 2)
        self.assertEqual(obj.method0(), 2)
        self.assertEqual(obj.method0(), 2)
        self.assertEqual(call_count, 1)

        Thread.sleep(seconds=CACHE_DURATION.seconds)

        self.assertEqual(obj.method0(), 2)
        self.assertEqual(obj.method0(), 2)
        self.assertEqual(obj.method0(), 2)
        self.assertEqual(obj.method0(), 2)
        self.assertEqual(call_count, 2)

    def test_param_cache(self):
        global call_count
        call_count = 0

        obj = MyType()

        self.assertEqual(obj.method1(0), "zero")
        self.assertEqual(obj.method1(1), "one")
        self.assertEqual(obj.method1(2), "big")
        self.assertEqual(obj.method1(3), "big")
        self.assertEqual(call_count, 4)

        self.assertEqual(obj.method1(0), "zero")
        self.assertEqual(obj.method1(1), "one")
        self.assertEqual(obj.method1(2), "big")
        self.assertEqual(obj.method1(3), "big")
        self.assertEqual(call_count, 4)

        Thread.sleep(seconds=CACHE_DURATION.seconds)

        self.assertEqual(obj.method1(0), "zero")
        self.assertEqual(obj.method1(1), "one")
        self.assertEqual(obj.method1(2), "big")
        self.assertEqual(obj.method1(3), "big")
        self.assertEqual(call_count, 8)

        self.assertEqual(obj.method1(0), "zero")
        self.assertEqual(obj.method1(1), "one")
        self.assertEqual(obj.method1(2), "big")
        self.assertEqual(obj.method1(3), "big")
        self.assertEqual(call_count, 8)



@cache
def forever_func():
    global call_count
    call_count += 1
    return 42

forever_func()

@cache(duration=CACHE_DURATION)
def single_func():
    global call_count
    call_count += 1
    return 42



class MyType(object):

    @cache(duration=CACHE_DURATION)
    def method0(self):
        global call_count
        call_count += 1
        return 2

    @cache(duration=CACHE_DURATION)
    def method1(self, param):
        global call_count
        call_count += 1

        if param == 0:
            return "zero"
        elif param == 1:
            return "one"
        else:
            return "big"

