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


par = os.sep + ".."


class TestNames(FuzzyTestCase):

    def test_relative_self(self):
        f = File(".")
        self.assertEqual(f.parent.filename, "..")
        self.assertEqual(f.parent.parent.filename, ".."+par)
        self.assertEqual(f.parent.parent.parent.filename, ".."+par+par)

    def test_relative_self2(self):
        f = File("")
        self.assertEqual(f.parent.filename, "..")
        self.assertEqual(f.parent.parent.filename, ".."+par)
        self.assertEqual(f.parent.parent.parent.filename, ".."+par+par)

    def test_relative_name(self):
        f = File("test.txt")
        self.assertEqual(f.parent.filename, "")
        self.assertEqual(f.parent.parent.filename, "..")
        self.assertEqual(f.parent.parent.parent.filename, ".."+par)

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
        test1 = join_path('/', 'this/is/a/test/')
        test2 = join_path('.', 'this/is/a/test/')
        test3 = join_path('', 'this/is/a/test/')
        test4 = join_path('/test', '.')
        test5 = join_path('/test', '..', 'this')
        test6 = join_path('/test', '../this')

        self.assertEqual(test1, '/this/is/a/test')
        self.assertEqual(test2, 'this/is/a/test')
        self.assertEqual(test3, 'this/is/a/test')
        self.assertEqual(test4, '/test')
        self.assertEqual(test5, '/this')
        self.assertEqual(test6, '/this')

    def test_abs_and_rel_pathson_file_objects(self):
        test1 = join_path(File('/'), 'this/is/a/test/')
        test2 = join_path(File('.'), 'this/is/a/test/')
        test3 = join_path(File(''), 'this/is/a/test/')
        test4 = join_path(File('/test'), '.')
        test5 = join_path(File('/test'), '..', 'this')
        test6 = join_path(File('/test'), '../this')

        self.assertEqual(test1, '/this/is/a/test')
        self.assertEqual(test2, 'this/is/a/test')
        self.assertEqual(test3, 'this/is/a/test')
        self.assertEqual(test4, '/test')
        self.assertEqual(test5, '/this')
        self.assertEqual(test6, '/this')
