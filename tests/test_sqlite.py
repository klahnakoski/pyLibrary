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
from unittest import skip

from mo_future import text_type
from mo_logs import Log
from mo_testing.fuzzytestcase import FuzzyTestCase
from mo_threads import Till, Thread

call_count = 0


class TestMeta(FuzzyTestCase):
    @skip("takes a long time")
    def test_sqlite_does_not_lock_gil(self):
        # USE THIS TEST TO VERIFY THE runner() IS GOING SAME SPEED WHILE DATABASE DOES ITS WORK
        def make_database(num, please_stop):
            db = sqlite3.connect(
                database=":memory:" if num == 1 else "this is a test file" + text_type(num) + ".sqlite",
                check_same_thread=False,
                isolation_level=None,
            )
            db.execute("DROP TABLE IF EXISTS digits" + text_type(num))
            db.execute("DROP TABLE IF EXISTS thousand" + text_type(num))
            db.execute("DROP TABLE IF EXISTS million" + text_type(num))
            db.execute("DROP TABLE IF EXISTS billion" + text_type(num))
            db.execute("CREATE TABLE digits" + text_type(num) + " (value TEXT)")

            Log.note("ten")
            db.execute(
                "INSERT INTO digits"
                + text_type(num)
                + " VALUES ('1'), ('2'), ('3'), ('4'), ('5'), ('6'), ('7'), ('8'), ('9')"
            )
            db.commit()
            Log.note("thousand")
            db.execute(
                "CREATE TABLE thousand"
                + text_type(num)
                + " AS SELECT d1.value || d2.value || d3.value AS value FROM digits"
                + text_type(num)
                + " d1, digits"
                + text_type(num)
                + " d2, digits"
                + text_type(num)
                + " d3"
            )
            Log.note("million")
            db.execute(
                "CREATE TABLE million"
                + text_type(num)
                + " AS SELECT d1.value || d2.value AS value FROM thousand"
                + text_type(num)
                + " d1, thousand"
                + text_type(num)
                + " d2"
            )
            Log.note("billion")
            db.execute(
                "CREATE TABLE billion"
                + text_type(num)
                + " AS SELECT d1.value || d2.value || d3.value AS value FROM thousand"
                + text_type(num)
                + " d1, thousand"
                + text_type(num)
                + " d2, thousand"
                + text_type(num)
                + " d3"
            )
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

        Log.note("First, we report the number of increments done by runner() each second:")
        run = Thread.run("", runner)
        rep = Thread.run("", reporter)

        Till(seconds=10).wait()
        Log.note("Second, we run some database updates:")
        t1 = Thread.run("1", make_database, 1)
        t2 = Thread.run("2", make_database, 2)
        # t3 = Thread.run("3", make_database, 3)

        t1.join()
        t2.join()
        # t3.join()

        Log.note("Done")
        run.please_stop.go()
        rep.please_stop.go()
