# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

import datetime
import unittest

from pyLibrary.debugs.logs import Log
from pyDots import wrap
from pyLibrary.jsons.encoder import pypy_json_encode
from pyLibrary.jsons.typed_encoder import typed_encode, json2typed


class TestJSON(unittest.TestCase):
    def test_date(self):
        value = {"test": datetime.date(2013, 11, 13)}
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "test": {"$value": 1384318800}}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)


    def test_unicode1(self):
        value = {"comment": u"Open all links in the current tab, except the pages opened from external apps â€” open these ones in new windows"}
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "comment": {"$value": "Open all links in the current tab, except the pages opened from external apps â€” open these ones in new windows"}}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_unicode2(self):
        value = {"comment": b"testing accented char àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"}
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "comment": {"$value": "testing accented char àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"}}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_unicode3(self):
        value = {"comment": u"testing accented char ŕáâăäĺćçčéęëěíîďđńňóôőö÷řůúűüýţ˙"}
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "comment": {"$value": "testing accented char ŕáâăäĺćçčéęëěíîďđńňóôőö÷řůúűüýţ˙"}}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_double(self):
        value = {"value": 5.2025595183536973e-07}
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "value": {"$value": 5.202559518353697e-7}}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_empty_list(self):
        value = {"value": []}
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "value": []}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_nested(self):
        value = {"a": {}, "b": {}}
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "a": {"$object": "."}, "b": {"$object": "."}}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_list_of_objects(self):
        value = {"a": [{}, "b"]}
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "a": [{"$object": "."}, {"$value": "b"}]}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_empty_list_value(self):
        value = []
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'[]'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_list_value(self):
        value = [42]
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'[{"$value": 42}]'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_list(self):
        value = {"value": [23, 42]}
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "value": [{"$value": 23}, {"$value": 42}]}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_number_value(self):
        value = 42
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = '{"$value": 42}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_empty_string_value(self):
        value = u""
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = '{"$value": ""}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_string_value(self):
        value = u"42"
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = '{"$value": "42"}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_escaped_string_value(self):
        value = "\""
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = '{"$value": "\\""}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_bad_key(self):
        test = {24: "value"}
        self.assertRaises(Exception, typed_encode, *[test])

    def test_false(self):
        value = False
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = '{"$value": false}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_true(self):
        value = True
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = '{"$value": true}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_null(self):
        value = None
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = '{"$value": null}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_empty_dict(self):
        value = wrap({"match_all": wrap({})})
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "match_all": {"$object": "."}}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_complex_object(self):
        value = wrap({"s": 0, "r": 5})
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "s": {"$value": 0}, "r": {"$value": 5}}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)


    def test_empty_list1(self):
        value = wrap({"a": []})
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "a": []}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

    def test_empty_list2(self):
        value = wrap({"a": [], "b": 1})
        test1 = typed_encode(value)
        test2 = json2typed(pypy_json_encode(value))
        expected = u'{"$object": ".", "a": [], "b": {"$value": 1}}'
        self.assertEqual(test1, expected)
        self.assertEqual(test2, expected)

