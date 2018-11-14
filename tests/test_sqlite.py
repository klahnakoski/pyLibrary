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

import sqlite3

from mo_future import text_type

from mo_logs import Log
from mo_testing.fuzzytestcase import FuzzyTestCase
from mo_threads import Till, Thread
from mo_times.durations import SECOND


call_count = 0


class TestMeta(FuzzyTestCase):

    def test_sqlite_does_not_lock_gil(self):
        def make_database(num, please_stop):
            db = sqlite3.connect(
                database="this is a test file.sqlite",
                check_same_thread=False,
                isolation_level=None
            )
            db.execute("DROP TABLE IF EXISTS digits"+text_type(num))
            db.execute("DROP TABLE IF EXISTS thousand"+text_type(num))
            db.execute("DROP TABLE IF EXISTS million"+text_type(num))
            db.execute("DROP TABLE IF EXISTS billion"+text_type(num))
            db.execute("CREATE TABLE digits"+text_type(num)+" (value TEXT)")

            Log.note("ten")
            db.execute("INSERT INTO digits"+text_type(num)+" VALUES ('1'), ('2'), ('3'), ('4'), ('5'), ('6'), ('7'), ('8'), ('9')")
            Log.note("thousand")
            db.execute("CREATE TABLE thousand"+text_type(num)+" AS SELECT d1.value || d2.value || d3.value AS value FROM digits d1, digits d2, digits d3")
            Log.note("million")
            db.execute("CREATE TABLE million"+text_type(num)+" AS SELECT d1.value || d2.value AS value FROM thousand d1, thousand d2")
            Log.note("billion")
            db.execute("CREATE TABLE billion"+text_type(num)+" AS SELECT d1.value || d2.value || d3.value AS value FROM thousand d1, thousand d2, thousand d3")
            Log.note("done")


        def runner(please_stop):
            global call_count
            while not please_stop:
                call_count += 1

        def reporter(please_stop):
            global call_count
            while not please_stop:
                c = call_count
                call_count = 0
                Log.note("call count={{count}}", count=c)
                Till(seconds=1).wait()

        run = Thread.run("", runner)
        rep = Thread.run("", reporter)

        Till(seconds=10).wait()
        Log.note("build database")
        t1 = Thread.run("1", make_database, 1)
        # t2 = Thread.run("2", make_database, 2)
        # t3 = Thread.run("3", make_database, 3)

        t1.join()
        # t2.join()
        # t3.join()

        Log.note("Done build")
        run.please_stop.go()
        rep.please_stop.go()
