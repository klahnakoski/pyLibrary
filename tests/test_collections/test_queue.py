# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import unicode_literals

from mo_collections.queue import Queue
from mo_testing.fuzzytestcase import FuzzyTestCase


class TestQueue(FuzzyTestCase):
    def test_add(self):
        test = Queue()

        test.add(1)
        self.assertEqual(test, [1])
        test.add(2)
        self.assertEqual(test, [1, 2])
        test.add(3)
        self.assertEqual(test, [1, 2, 3])

    def test_push(self):
        test = Queue()

        test.push(1)
        self.assertEqual(test, [1])
        test.push(2)
        self.assertEqual(test, [2, 1])
        test.push(3)
        self.assertEqual(test, [3, 2, 1])

    def test_push_existing(self):
        test = Queue()
        test.extend([1, 2, 3])

        test.push(3)
        self.assertEqual(test, [3, 1, 2])

    def test_pop(self):
        test = Queue()
        test.extend([1, 2, 3, 2])

        self.assertEqual(test.pop(), 1)
        self.assertEqual(test.pop(), 2)
        self.assertEqual(test.pop(), 3)
        self.assertEqual(len(test), 0)
