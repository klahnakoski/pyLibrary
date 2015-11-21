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
from __future__ import division
from __future__ import absolute_import
from pyLibrary import strings

from pyLibrary.strings import expand_template
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.thread.threads import Lock, Thread, Signal
from pyLibrary.times.dates import Date
from pyLibrary.times.durations import SECOND


class TestThreads(FuzzyTestCase):
    def setUp(self):
        pass

    def test_lock_wait_timeout(self):
        locker = Lock("test")

        def take_lock(please_stop):
            with locker:
                locker.wait(1)
                locker.wait(SECOND)
                locker.wait(till=Date.now()+SECOND)

        Thread.run("take lock", take_lock)
