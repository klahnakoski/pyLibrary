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
import unittest
from pyLibrary.env.logs import Log, Except
from pyLibrary.structs.wraps import wrap, listwrap


class TestExcept(unittest.TestCase):

    def test_trace_of_simple_raises(self):
        try:
            problem_a()
        except Exception, e:
            f = Except.wrap(e)
            self.assertEqual(f.template, "expected exception")
            for i, m in enumerate(listwrap(f.trace).method):
                if m == "test_trace_of_simple_raises":
                    self.assertEqual(i, 2)
                    break
            else:
                self.fail("expecting stack to show this method")

    def test_full_trace_exists(self):
        try:
            problem_a2()
        except Exception, e:
            cause = e.cause[0]
            self.assertEqual(cause.template, "expected exception")

            for i, m in enumerate(listwrap(cause.trace).method):
                if m == "test_full_trace_exists":
                    self.assertEqual(i, 2)
                    break
            else:
                self.fail("expecting stack to show this method")

    def test_full_trace_on_wrap(self):
        try:
            problem_b()
        except Exception, e:
            cause = Except.wrap(e)
            self.assertEqual(cause.template, "expected exception")

            for i, m in enumerate(listwrap(cause.trace).method):
                if m == "test_full_trace_on_wrap":
                    self.assertEqual(i, 1)
                    break
            else:
                self.fail("expecting stack to show this method")


def problem_a():
    problem_b()

def problem_b():
    raise Exception("expected exception")


def problem_a2():
    try:
        problem_b()
    except Exception, e:
        Log.error("this is a problem", e)



if __name__ == '__main__':
    try:
        Log.start()
        unittest.main()
    finally:
        Log.stop()
