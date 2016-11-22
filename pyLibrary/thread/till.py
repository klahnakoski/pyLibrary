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
from time import sleep as _sleep

from pyLibrary.thread.signal import Signal
from pyLibrary.times.dates import Date
from pyLibrary.times.durations import Duration

INTERVAL = 0.1


class Till(Signal):
    """
    TIMEOUT AS A SIGNAL
    """
    all_timers = []
    dirty = False
    locker = thread.allocate_lock()

    def __init__(self, till=None, timeout=None, seconds=None):
        Signal.__init__(self, "a timeout")
        if till != None:
            timeout = Date(till).unix
        elif timeout != None:
            timeout = (Date.now()+Duration(timeout)).unix
        elif seconds != None:
            timeout = Date.now().unix + seconds

        with Till.locker:
            Till.all_timers.append((timeout, self))
            Till.dirty = True

    @classmethod
    def daemon(cls, please_stop):
        next_ping = Date.now().unix
        try:
            while not please_stop:
                now = Date.now().unix
                if Till.dirty or next_ping < now:
                    next_ping = now + INTERVAL
                    work = None
                    with Till.locker:
                        if Till.all_timers:
                            Till.all_timers.sort(key=lambda r: r[0])
                            for i, (t, s) in enumerate(Till.all_timers):
                                if now > t:
                                    work, Till.all_timers[:i] = Till.all_timers[:i], []
                                    next_ping = min(next_ping, Till.all_timers[0][0])
                                    break
                            else:
                                work, Till.all_timers = Till.all_timers, []

                        Till.dirty = False
                    if work:
                        for t, s in work:
                            s.go()
                else:
                    _sleep(min(next_ping-now, INTERVAL))
        except Exception, e:
            from pyLibrary.debugs.logs import Log

            Log.warning("timer shutdown", cause=e)

