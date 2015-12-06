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
from future.utils import raise_from

import logging
import unittest

from pyLibrary import convert
from pyLibrary.debugs.log_usingQueue import TextLog_usingQueue
from pyLibrary.debugs.logs import Log, Except
from pyLibrary.dot import listwrap, wrap
from pyLibrary.dot.objects import DictObject
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.thread.threads import Thread


class TestExcept(FuzzyTestCase):
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
            cause = e.cause
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


    def test_warning_keyword_parameters(self):
        a = {"c": "a", "b": "d"}
        b = {"c": "b"}
        params = {"a": a, "b": b}

        WARNING = 'WARNING: test'
        CAUSE = '\ncaused by\n\tERROR: problem'
        A = '{\n    "b": "d",\n    "c": "a"\n}'
        B = '{"c": "b"}'
        AC = 'a'
        AB = 'd'
        BC = 'b'

        log_queue = TextLog_usingQueue("abba")
        backup_log, Log.main_log = Log.main_log, log_queue

        try:
            raise Exception("problem")
        except Exception, e:
            Log.warning("test")
            self.assertEqual(Log.main_log.pop(), WARNING)

            Log.warning("test: {{a}}", a=a)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A)

            Log.warning("test: {{a}}: {{b}}", a=a, b=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A + ': ' + B)

            Log.warning("test", e)
            self.assertEqual(Log.main_log.pop(), WARNING + CAUSE)

            Log.warning("test: {{a}}", a=a, cause=e)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A + CAUSE)

            Log.warning("test: {{a}}: {{b}}", a=a, b=b, cause=e)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A + ': ' + B + CAUSE)

            Log.warning("test: {{a}}", e, a=a)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A + CAUSE)

            Log.warning("test: {{a}}: {{b}}", e, a=a, b=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A + ': ' + B + CAUSE)

            Log.warning("test: {{a}}", params, e)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A + CAUSE)

            Log.warning("test: {{a}}: {{b}}", params, e)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A + ': ' + B + CAUSE)

            Log.warning("test: {{a}}: {{b}}", params, e, a=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + B + ': ' + B + CAUSE)

            Log.warning("test: {{a}}: {{b}}", wrap(params), e, a=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + B + ': ' + B + CAUSE)

            Log.warning("test: {{a.c}}", a=a)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + AC)

            Log.warning("test: {{a.c}}: {{a.b}}", a=a, b=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + AC + ': ' + AB)

            Log.warning("test: {{a.c}}: {{b.c}}", a=a, b=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + AC + ': ' + BC)

            Log.warning("test: {{a.c}}", a=a, cause=e)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + AC + CAUSE)

            Log.warning("test: {{a.c}}: {{b.c}}", a=a, b=b, cause=e)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + AC + ': ' + BC + CAUSE)
        finally:
            Log.main_log = backup_log


    def test_note_keyword_parameters(self):
        a = {"c": "a", "b": "d"}
        b = {"c": "b"}
        params = {"a": a, "b": b}

        WARNING = 'test'
        A = '{\n    "b": "d",\n    "c": "a"\n}'
        B = '{"c": "b"}'
        AC = 'a'
        AB = 'd'
        BC = 'b'

        # DURING TESTING SOME OTHER THREADS MAY STILL BE WRITING TO THE LOG
        Thread.sleep(1)
        # HIGHJACK LOG FOR TESTING OUTPUT
        log_queue = TextLog_usingQueue()
        backup_log, Log.main_log = Log.main_log, log_queue

        try:
            raise Exception("problem")
        except Exception, e:
            Log.note("test")
            self.assertEqual(Log.main_log.pop(), WARNING)

            Log.note("test: {{a}}", a=a)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A)

            Log.note("test: {{a}}: {{b}}", a=a, b=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A + ': ' + B)

            Log.note("test: {{a.c}}", a=a)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + AC)

            Log.note("test: {{a}}: {{b}}", params)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + A + ': ' + B)

            Log.note("test: {{a}}: {{b}}", params, a=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + B + ': ' + B)

            Log.note("test: {{a}}: {{b}}", wrap(params), a=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + B + ': ' + B)

            Log.note("test: {{a.c}}: {{a.b}}", a=a, b=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + AC + ': ' + AB)

            Log.note("test: {{a.c}}: {{b.c}}", a=a, b=b)
            self.assertEqual(Log.main_log.pop(), WARNING + ': ' + AC + ': ' + BC)
        finally:
            Log.main_log = backup_log


    #NORMAL RAISING
    def test_python_raise_from(self):
        def problem_y():
            raise Exception("this is the root cause")

        def problem_x():
            try:
                problem_y()
            except Exception, e:
                raise_from(Exception("this is a problem"), e)

        try:
            problem_x()
        except Exception, e:
            class _catcher(logging.Handler):
                def handle(self, record):
                    o = convert.value2json(DictObject(record))
                    if record:
                        pass
                    if "this is a problem" not in e:
                        Log.error("We expect Python to, at least, report the first order problem")
                    if "this is the root cause" in e:
                        Log.error("We do not expect Python to report exception chains")

            log=logging.getLogger()
            log.addHandler(_catcher())
            log.exception("problem")

    #NORMAL RE-RAISE
    def test_python_re_raise(self):
        def problem_y():
            raise Exception("this is the root cause")

        def problem_x():
            try:
                problem_y()
            except Exception, f:
                raise f

        try:
            problem_x()
        except Exception, e:
            e = Except.wrap(e)
            self.assertEqual(e.cause, None)  # REALLY, THE CAUSE IS problem_y()



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
