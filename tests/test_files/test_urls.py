# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import Null
from mo_json import true, false
from mo_logs import Log
from mo_testing.fuzzytestcase import FuzzyTestCase

from mo_files.url import url_param2value, value2url_param, URL, from_paths


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
            {"value": {"one": {"two": [{"test": 1}, {"test": 2}, "3"]}}},
        ]

        for r in reversable:
            self.assertEqual(url_param2value(value2url_param(r)), r)

    def test_encoding(self):
        to_query = [
            [{"a": None}, ""],
            [{"a": [1, None, ""]}, "a=1"],
            [{"a": " "}, "a=+"],
            [{"a": "  "}, "a=++"],
            [{"a": [1, "alpha"]}, "a=1,alpha"],
            [{"a": {"b": [1, "alpha"]}}, "a.b=1,alpha"],
            [{"a": '{"a": 1}'}, 'a="%7b\\"a\\":+1%7d"'],
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
        self.assertTrue(url_param2value("a")["a"])
        self.assertTrue(URL("/jobs?").query != None)

    def test_decode_complex(self):
        content = "draw=1&columns%5B0%5D%5Bdata%5D=0&columns%5B0%5D%5Bname%5D=&columns%5B0%5D%5Bsearchable%5D=true&columns%5B0%5D%5Borderable%5D=true&columns%5B0%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B0%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B1%5D%5Bdata%5D=1&columns%5B1%5D%5Bname%5D=&columns%5B1%5D%5Bsearchable%5D=true&columns%5B1%5D%5Borderable%5D=true&columns%5B1%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B1%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B2%5D%5Bdata%5D=2&columns%5B2%5D%5Bname%5D=&columns%5B2%5D%5Bsearchable%5D=true&columns%5B2%5D%5Borderable%5D=true&columns%5B2%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B2%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B3%5D%5Bdata%5D=3&columns%5B3%5D%5Bname%5D=&columns%5B3%5D%5Bsearchable%5D=true&columns%5B3%5D%5Borderable%5D=true&columns%5B3%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B3%5D%5Bsearch%5D%5Bregex%5D=false&columns%5B4%5D%5Bdata%5D=4&columns%5B4%5D%5Bname%5D=&columns%5B4%5D%5Bsearchable%5D=true&columns%5B4%5D%5Borderable%5D=true&columns%5B4%5D%5Bsearch%5D%5Bvalue%5D=&columns%5B4%5D%5Bsearch%5D%5Bregex%5D=false&start=0&length=25&search%5Bvalue%5D=&search%5Bregex%5D=false&search%5BcaseInsensitive%5D=true&search%5Bsmart%5D=true&escape=true"
        value = url_param2value(content)
        struct = from_paths(value)
        Log.note("{{data|json}}", data=struct)
        expected = {
            "columns": [
                {
                    "data": 0,
                    "name": "",
                    "orderable": true,
                    "search": {"regex": false, "value": ""},
                    "searchable": true,
                },
                {
                    "data": 1,
                    "name": "",
                    "orderable": true,
                    "search": {"regex": false, "value": ""},
                    "searchable": true,
                },
                {
                    "data": 2,
                    "name": "",
                    "orderable": true,
                    "search": {"regex": false, "value": ""},
                    "searchable": true,
                },
                {
                    "data": 3,
                    "name": "",
                    "orderable": true,
                    "search": {"regex": false, "value": ""},
                    "searchable": true,
                },
                {
                    "data": 4,
                    "name": "",
                    "orderable": true,
                    "search": {"regex": false, "value": ""},
                    "searchable": true,
                },
            ],
            "draw": 1,
            "escape": true,
            "length": 25,
            "search": {
                "caseInsensitive": true,
                "regex": false,
                "smart": true,
                "value": "",
            },
            "start": 0,
        }
        self.assertAlmostEqual(struct, expected)

    def test_reversable2(self):
        r = {"value": {"one": {"two": [{"test": 1}, {"test": 2}, "3"]}}}
        self.assertEqual(url_param2value(value2url_param(r)), r)

    def test_add_query(self):
        a = URL("https://example.com/path?x=1")
        b = a + {"y": 2}
        self.assertTrue(a.query.y == None)
        self.assertEqual(b.query, {"x": 1, "y": 2})

    def test_from_mo_json_config(self):
        url = 'file:///C:/Users/kyle/code/mo-json-config/tests/resources/test_ref_w_parameters.json?metadata=a,b'
        result = URL(url)
        self.assertEqual(result.query.metadata, ['a', 'b'])
