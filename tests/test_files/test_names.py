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

import os

from mo_files import File, join_path
from mo_testing.fuzzytestcase import FuzzyTestCase


par = "/.."


class TestNames(FuzzyTestCase):
    def test_relative_self(self):
        f = File(".")
        self.assertEqual(f.parent.filename, "..")
        self.assertEqual(f.parent.parent.filename, ".." + par)
        self.assertEqual(f.parent.parent.parent.filename, ".." + par + par)

    def test_relative_self2(self):
        f = File("")
        self.assertEqual(f.parent.filename, "..")
        self.assertEqual(f.parent.parent.filename, ".." + par)
        self.assertEqual(f.parent.parent.parent.filename, ".." + par + par)

    def test_relative_name(self):
        f = File("test.txt")
        self.assertEqual(f.parent.filename, "")
        self.assertEqual(f.parent.parent.filename, "..")
        self.assertEqual(f.parent.parent.parent.filename, ".." + par)

    def test_relative_path(self):
        f = File("a/test.txt")
        self.assertEqual(f.parent.filename, "a")
        self.assertEqual(f.parent.parent.filename, "")
        self.assertEqual(f.parent.parent.parent.filename, "..")

    def test_grandparent(self):
        f = File.new_instance("tests/temp", "../..")
        self.assertEqual(f.filename, ".")

    def test_concat(self):
        f = File.new_instance("tests/temp") / "something" / "or" / "other"
        self.assertTrue(f.abspath.endswith("/tests/temp/something/or/other"))

    def test_empty(self):
        test = join_path("test", "")
        self.assertEqual(test, "test")

    def test_parents(self):
        test = join_path("test", "../../..")
        self.assertEqual(test, "../..")
        self.assertRaises(Exception, join_path, "/test", "../../..")
        self.assertRaises(Exception, join_path, "/test", "../..")

    def test_abs_and_rel_paths(self):
        test1 = join_path("/", "this/is/a/test/")
        test2 = join_path(".", "this/is/a/test/")
        test3 = join_path("", "this/is/a/test/")
        test4 = join_path("/test", ".")
        test5 = join_path("/test", "..", "this")
        test6 = join_path("/test", "../this")

        self.assertEqual(test1, "/this/is/a/test")
        self.assertEqual(test2, "this/is/a/test")
        self.assertEqual(test3, "this/is/a/test")
        self.assertEqual(test4, "/test")
        self.assertEqual(test5, "/this")
        self.assertEqual(test6, "/this")

    def test_abs_and_rel_pathson_file_objects(self):
        test1 = join_path(File("/"), "this/is/a/test/")
        test2 = join_path(File("."), "this/is/a/test/")
        test3 = join_path(File(""), "this/is/a/test/")
        test4 = join_path(File("/test"), ".")
        test5 = join_path(File("/test"), "..", "this")
        test6 = join_path(File("/test"), "../this")

        self.assertEqual(test1, "/this/is/a/test")
        self.assertEqual(test2, "this/is/a/test")
        self.assertEqual(test3, "this/is/a/test")
        self.assertEqual(test4, "/test")
        self.assertEqual(test5, "/this")
        self.assertEqual(test6, "/this")

    def test_home_path(self):
        home_path = os.path.expanduser("~").replace(os.sep, "/")
        test1 = File("~")
        test2 = File("~/")
        test3 = File("~/test.json")
        test4 = File("~test.json")
        test5 = File("~") / "test.json"

        self.assertEqual(test1.filename, home_path + "/")
        self.assertEqual(test2.filename, home_path + "/")
        self.assertEqual(test3.filename, home_path + "/test.json")
        self.assertEqual(test4.filename, home_path + "/test.json")
        self.assertEqual(test5.filename, home_path + "/test.json")

    def test_extension(self):
        test1 = File("test.json")
        test2 = test1.add_extension("gz")
        test3 = test1.set_extension("gz")

        self.assertEqual(test1.filename, "test.json")
        self.assertEqual(test2.filename, "test.json.gz")
        self.assertEqual(test3.filename, "test.gz")

    def test_suffix(self):
        test1 = File("tools/test.json")
        test2 = test1.add_suffix(".backup")
        test3 = test1.add_suffix("-backup")
        test4 = test1.set_name("other")

        self.assertEqual(test1.filename, "tools/test.json")
        self.assertEqual(test2.filename, "tools/test.backup.json")
        self.assertEqual(test3.filename, "tools/test.-backup.json")
        self.assertEqual(test4.filename, "tools/other.json")
