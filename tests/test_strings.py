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

from pyLibrary.strings import expand_template
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase


class TestCNV(FuzzyTestCase):
    def setUp(self):
        pass

    def test_right_align(self):
        total = 123.45
        some_list = [10, 11, 14, 80]
        details = {"person": {"name": "Kyle Lahnakoski", "age": 40}}

        result = expand_template("it is currently {{now|datetime}}", {"now": 1420119241000})
        self.assertEqual(result, 'it is currently 2015-01-01 13:34:01')

        result = expand_template("Total: {{total|right_align(20)}}", {"total": total})
        self.assertEqual(result, 'Total:               123.45')

        result = expand_template("Summary:\n{{list|json|indent}}", {"list": some_list})
        self.assertEqual(result, 'Summary:\n\t[10, 11, 14, 80]')

        result = expand_template("Summary:\n{{list|indent}}", {"list": some_list})
        self.assertEqual(result, 'Summary:\n\t[10, 11, 14, 80]')

        result = expand_template("{{person.name}} is {{person.age}} years old", details)
        self.assertEqual(result, "Kyle Lahnakoski is 40 years old")


