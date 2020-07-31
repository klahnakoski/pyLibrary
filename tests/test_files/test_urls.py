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

from mo_dots import Null

from mo_files.url import url_param2value, value2url_param, URL
from mo_testing.fuzzytestcase import FuzzyTestCase


class TestURLs(FuzzyTestCase):
    def test_reversable(self):
        reversable = [
            {"a": "{}"},
            {"a": "[]"},
            {"a": "\\"},
            {"a": '"'},
            {"a": "%"},
            {"a": "+"},
            {"a": "="},
            {"a": "=a"},
            {"a": "null"},
            {"a": False},
            {"a": "false"},
            {"a": True},
            {"a": "true"},
            {"a": 42},
            {"a": "42"},
            {"a": " "},
            {"a": "  "},
            {"a": "blue+light blue"},
            {"a": '{"test":42}'},
            {"a": {"test": 42}},
            {"a": [1, 2, 3]},
            {"a": {"b": {"c": 42}}},
            {"a": "test"},
            {"a": "a b"},
            {"a": "a b c d"},
            {"a": "ståle"},
            {"/jobs": True},
            {"/jobs?": True},
        ]

        for r in reversable:
            self.assertEqual(url_param2value(value2url_param(r)), r)

    def test_encoding(self):
        to_query = [
            # [{"a": None}, ""],
            # [{"a": [1, None, ""]}, "a=1"],
            [{"a": " "}, "a=+"],
            [{"a": "  "}, "a=++"],
            [{"a": [1, "alpha"]}, "a=1,alpha"],
            [{"a": {"b": [1, "alpha"]}}, "a.b=1,alpha"]
        ]

        for q, e in to_query:
            self.assertEqual(value2url_param(q), e)

    def test_non_standard(self):
        non_standard_query_strings = [
            [{"a": " "}, "a=%20"],
            [{"a": "  "}, "a=%20%20"],
            [{"a": "blue+light blue"}, "a=blue%2Blight%20blue"],
            [{}, ""],
            [{"a": True}, "a=true"],
            [{"a": None}, "a=null"],
            [{"a": Null}, "a=null"],
            [{"a": "%"}, "a=%"],
            [{"a": "%%%%"}, "a=%%25%%"],
            [{"a": "%abåle%"}, "a=%ab%C3%A5le%"],
            [{"a": "å%able%"}, "a=%C3%A5%able%"],
            [{"a": "{%ab|%de}"}, "a=%7B%ab%7C%de%7D"],
            [{"a": "{%ab%|%de%}"}, "a=%7B%ab%%7C%de%%7D"],
            [{"a": "%7 B%ab%|%de%%7 D"}, "a=%7 B%ab%%7C%de%%7 D"],
            [{"a": "%ab"}, "a=%ab"],
            [{"a": "%ab%ab%ab"}, "a=%ab%ab%ab"],
            [{"a": "a MM"}, "a=%61+%4d%4D"],
            [{"a": "ståle%"}, "a=st%C3%A5le%"],
            [{"a": "%ståle%"}, "a=%st%C3%A5le%"],
            [{"a": "%{ståle}%"}, "a=%%7Bst%C3%A5le%7D%"],
            [{"a": "\uFEFFtest"}, "a=%EF%BB%BFtest"],
            [{"a": "\uFEFF"}, "a=%EF%BB%BF"],
            [{"a": "†"}, "a=†"],
        ]

        for e, s in non_standard_query_strings:
            self.assertEqual(url_param2value(s), e)

    def test_no_value_is_truthy(self):
        self.assertTrue(url_param2value("a")['a'])
        self.assertTrue(URL("/jobs?").query!=None)
