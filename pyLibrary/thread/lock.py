# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
# THIS THREADING MODULE IS PERMEATED BY THE please_stop SIGNAL.
# THIS SIGNAL IS IMPORTANT FOR PROPER SIGNALLING WHICH ALLOWS
# FOR FAST AND PREDICTABLE SHUTDOWN AND CLEANUP OF THREADS

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import thread
from collections import deque


from pyLibrary.thread.signal import Signal

_Log = None
_Except = None
_Thread = None
DEBUG = True
DEBUG_SIGNAL = False


def _late_import():
    global _Log
    global _Except
    global _Thread

    if _Thread:
        return

    from pyLibrary.debugs.logs import Log as _Log
    from pyLibrary.debugs.exceptions import Except as _Except
    from pyLibrary.thread.threads import Thread as _Thread

    _ = _Log
    _ = _Except
    _ = _Thread


class Lock(object):
    """
    SIMPLE LOCK (ACTUALLY, A PYTHON threadind.Condition() WITH notify() BEFORE EVERY RELEASE)
    """
    __slots__ = ["name", "lock", "waiting"]

    def __init__(self, name=""):
        self.name = name
        self.lock = thread.allocate_lock()
        self.waiting = deque()

    def __enter__(self):
        # with pyLibrary.times.timer.Timer("get lock"):
        self.lock.acquire()
        return self

    def __exit__(self, a, b, c):
        if self.waiting:
            waiter = self.waiting.pop()
            waiter.go()
        self.lock.release()

    def wait(self, till=None):
        if self.waiting:
            waiter = self.waiting.pop()
            waiter.go()

        if DEBUG:
            _late_import()
            _Log.note("make signal for "+_Thread.current().name)
            waiter = Signal(_Thread.current().name+" waiting")
            self.waiting.appendleft(waiter)
            self.lock.release()

            _Log.note("wait on {{lock|quote}}", lock=waiter.name)
            (waiter | till).wait_for_go()

            _Log.note("resumed from wait "+_Thread.current().name)
            if waiter:
                self.lock.acquire()
                return True
            return False
        else:
            waiter = Signal()
            self.waiting.appendleft(waiter)
            self.lock.release()

            (waiter | till).wait_for_go()

            if waiter:
                self.lock.acquire()
                return True
            return False
