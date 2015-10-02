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
from __future__ import absolute_import

from io import BytesIO

from pyLibrary.jsons import stream
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase


class TestJsonStream(FuzzyTestCase):
    def test_select_from_list(self):
        json = slow_stream('{"1":[{"a":"b"}]}')
        result = list(stream.parse(json, "1", ["1.a"]))
        expected = [{"1":{"a": "b"}}]
        self.assertEqual(result, expected)


    def test_select_nothing_from_many_list(self):
        json = slow_stream('{"1":[{"a":"b"}, {"a":"c"}]}')

        result = list(stream.parse(json, "1"))
        expected = [
            {},
            {}
        ]
        self.assertEqual(result, expected)

    def test_select_from_many_list(self):
        json = slow_stream('{"1":[{"a":"b"}, {"a":"c"}]}')

        result = list(stream.parse(json, "1", ["1.a"]))
        expected = [
            {"1": {"a": "b"}},
            {"1": {"a": "c"}}
        ]
        self.assertEqual(result, expected)

    def test_select_from_diverse_list(self):
        json = slow_stream('{"1":["test", {"a":"c"}]}')

        result = list(stream.parse(json, "1", ["1.a"]))
        expected = [
            {"1": {}},
            {"1": {"a": "c"}}
        ]
        self.assertEqual(result[0]["1"], None)
        self.assertEqual(result, expected)

    def test_select_from_deep_many_list(self):
        #                   0123456789012345678901234567890123
        json = slow_stream('{"1":{"2":[{"a":"b"}, {"a":"c"}]}}')

        result = list(stream.parse(json, "1.2", ["1.2.a"]))
        expected = [
            {"1": {"2": {"a": "b"}}},
            {"1": {"2": {"a": "c"}}}
        ]
        self.assertEqual(result, expected)

    def test_post_properties_error(self):
        json = slow_stream('{"0":"v", "1":[{"a":"b"}, {"a":"c"}], "2":[{"a":"d"}, {"a":"e"}]}')

        def test():
            result = list(stream.parse(json, "1", ["0", "1.a", "2"]))
        self.assertRaises(Exception, test)

    # def test_big_baddy(self):
    #     response = http.get("http://builddata.pub.build.mozilla.org/builddata/buildjson/builds-2015-09-20.js.gz", stream=True)
    #
    #     def json():
    #         return response.raw.read(MIN_READ_SIZE, decode_content=True)
    #
    #     for j in stream.parse(json, "builds", ["builds"]):
    #         Log.note("{{json|json}}", json=j)

    def test_constants(self):
        #                    01234567890123456789012345678901234567890123456789012345678901234567890123456789
        json = slow_stream(u'[true, false, null, 42, 3.14, "hello world", "àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"]')

        result = list(stream.parse(json, None, ["."]))
        expected = [True, False, None, 42, 3.14, u"hello world", u"àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"]
        self.assertEqual(result, expected)


def slow_stream(bytes):
    if isinstance(bytes, unicode):
        bytes = bytes.encode("utf8")

    r = BytesIO(bytes).read
    def output():
        return r(1)
    return output
