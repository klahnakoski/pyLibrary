# encoding: utf-8
#
#  This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import unicode_literals
import unittest
from util import struct
from util.cnv import CNV
from util.queries import Q
from util.struct import wrap, Struct


class TestQ(unittest.TestCase):
    def test_groupby(self):
        data = []
        for g, d in Q.groupby(data, size=5):
            assert False

        data = [1, 2, 3]
        for g, d in Q.groupby(data, size=5):
            assert d == [1, 2, 3]

        data = [1, 2, 3, 4, 5]
        for g, d in Q.groupby(data, size=5):
            assert d == [1, 2, 3, 4, 5]

        data = [1, 2, 3, 4, 5, 6]
        for g, d in Q.groupby(data, size=5):
            assert d == [1, 2, 3, 4, 5] or d == [6]

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        for g, d in Q.groupby(data, size=5):
            assert d == [1, 2, 3, 4, 5] or d == [6, 7, 8, 9]


    def test_select_w_dot(self):
        data = [{
            "sustained_result": {
                "diff": 2.2356859541328733,
                "confidence": 0.85313030049257099
            },
            "point_result": {
                "diff": -1.3195117613213274,
                "confidence": 0.15889902861667249
            }
        }]

        result = Q.select(data, "point_result.confidence")
        assert result[0] == 0.15889902861667249, "problem pulling deep values"

        result = Q.select(data, ["point_result.confidence", "sustained_result.confidence"])
        expected = {"point_result": {"confidence": 0.15889902861667249}, "sustained_result": {"confidence": 0.85313030049257099}}
        assert CNV.object2JSON(result[0]) == CNV.object2JSON(expected)

    def test_depth_select(self):
        data = [{
            "bug_id": 123,
            "attachments": [
                {"attach_id": 456, "name": "test1"},
                {"attach_id": 789, "name": "test2"}
            ]
        }, {
            "bug_id": 012,
            "attachments": [
                {"attach_id": 345, "name": "test3"}
            ]
        }]

        result = Q.select(data, "attachments.attach_id")
        self.assertItemsEqual(result, [456, 789, 345], "can not pull children")

        result = Q.select(data, ["bug_id", "attachments.name"])
        expected = [
            {"bug_id": 123, "attachments": {"name": "test1"}},
            {"bug_id": 123, "attachments": {"name": "test2"}},
            {"bug_id": 012, "attachments": {"name": "test3"}}
        ]
        assert CNV.object2JSON(result) == CNV.object2JSON(expected), "expecting complex result"


    def test_renaming(self):
        data = [{
            "bug_id": 123,
            "attachments": [
                {"attach_id": 456, "name": "test1"},
                {"attach_id": 789, "name": "test2"}
            ]
        }, {
            "bug_id": 012,
            "attachments": [
                {"attach_id": 345, "name": "test3"}
            ]
        }]

        result = Q.select(data, [{"name": "id", "value": "attachments.attach_id"}])
        expected = [{"id": 456}, {"id": 789}, {"id": 345}]
        assert CNV.object2JSON(result) == CNV.object2JSON(expected), "can not rename fields"

        result = Q.select(data, {"name": "id", "value": "attachments.attach_id"})
        self.assertItemsEqual(result, [456, 789, 345], "can not pull simple fields")

        result = Q.select(data, [{"name": "attach.id", "value": "attachments.attach_id"}])
        expected = [{"attach": {"id": 456}}, {"attach": {"id": 789}}, {"attach": {"id": 345}}]
        assert CNV.object2JSON(result) == CNV.object2JSON(expected), "can not rename fields"


    def test_unicode_attribute(self):
        value = wrap({})
        value["é"] = "test"

        dict_value = struct.unwrap(value)
        assert dict_value[u"é"] == "test", "not expecting problems"
        assert dict_value["é"] == "test", "not expecting problems"


    def test_simple_depth_filter(self):
        data = [Struct(**{u'test_build': {u'name': u'Firefox'}})]
        result = Q.filter(data, {u'term': {u'test_build.name': u'Firefox'}})
        assert len(result) == 1


    def test_split_filter(self):
        data = [{u'testrun': {u'suite': u'tp5o'}, u'result': {u'test_name': u'digg.com'}}]
        result = Q.filter(data, {u'and': [{u'term': {u'testrun.suite': u'tp5o'}}, {u'term': {u'result.test_name': u'digg.com'}}]})
        assert len(result) == 1
