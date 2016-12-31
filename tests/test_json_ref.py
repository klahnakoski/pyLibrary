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
import os
from pyLibrary import jsons
from pyDots import Data
from pyLibrary.env.files import File
from pyLibrary.parsers import URL
from pyLibrary.strings import expand_template
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase


class TestRef(FuzzyTestCase):
    def test_doc1(self):
        os.environ["test_variable"] = "abc"

        doc = jsons.ref.get("file://tests/resources/json_ref/test_ref1.json")

        self.assertEqual(doc.env_variable, "abc")
        self.assertEqual(doc.relative_file1, "*_ts")
        self.assertEqual(doc.relative_file2, "*_ts")
        self.assertEqual(doc.relative_doc, "value")
        self.assertEqual(doc.absolute_doc, "another value")
        self.assertEqual(doc.env_variable, "abc")
        self.assertEqual(doc.relative_object_doc, {"key": "new value", "another_key": "another value"})

    def test_doc2(self):
        # BETTER TEST OF RECURSION
        doc = jsons.ref.get("file://tests/resources/json_ref/test_ref2.json")

        self.assertEqual(doc, {
            "a": "some_value",
            "test_key": "test_value",
            "b": {
                "test_key": "test_value"
            }
        })

    def test_empty_object_as_json_parameter(self):
        url = "file://tests/resources/json_ref/test_ref_w_parameters.json?{{.|url}}"
        url = expand_template(url, {"metadata": Data()})
        result = jsons.ref.get(url)
        self.assertEqual(result, {"test_result": {}}, "expecting proper parameter expansion")

    def test_json_parameter(self):
        url = "file://tests/resources/json_ref/test_ref_w_parameters.json?{{.|url}}"
        url = expand_template(url, {"metadata": ["a", "b"]})
        result = jsons.ref.get(url)
        self.assertEqual(result, {"a": ["a", "b"]}, "expecting proper parameter expansion")

    def test_parameter_list(self):
        url = "file://tests/resources/json_ref/test_ref_w_parameters.json?test1=a&test1=b&test2=c&test1=d"
        self.assertEqual(URL(url).query, {"test1": ["a", "b", "d"], "test2": "c"}, "expecting test1 to be an array")

    def test_inner_doc(self):
        doc = jsons.ref.get("file://tests/resources/json_ref/inner.json")

        self.assertEqual(doc, {
            "area": {
                "color": {"description": "css color"},
                "border": {"properties": {"color": {"description": "css color"}}}
            },
            "definitions": {
                "object_style": {
                    "color": {"description": "css color"},
                    "border": {"properties": {"color": {"description": "css color"}}}
                },
                "style": {"properties": {"color": {"description": "css color"}}}
            }
        }, "expecting proper expansion")

    def test_read_home(self):
        file = "~/___test_file.json"
        source = "tests/resources/json_ref/simple.json"
        File.copy(File(source), File(file))
        content = jsons.ref.get("file://"+file)

        try:
            self.assertEqual(
                content,
                {"test_key": "test_value"}
            )
        finally:
            File(file).delete()

    def test_array_expansion(self):
        # BETTER TEST OF RECURSION
        doc = jsons.ref.get("file://tests/resources/json_ref/test_array.json")

        self.assertEqual(doc, {
            "a": "some_value",
            "list": {"deep": [
                {
                    "a": "a",
                    "test_key": "test_value"
                },
                {
                    "a": "b",
                    "test_key": "test_value"
                },
                {
                    "a": "c",
                    "test_key": "test_value"
                },
                {
                    "a": "d",
                    "test_key": "test_value"
                },
                {
                    "a": "e",
                    "test_key": "test_value"
                }
            ]}
        })

    def test_grandparent_reference(self):
        doc = jsons.ref.get("file://tests/resources/json_ref/child/grandchild/simple.json")

        self.assertEqual(doc, {"test_key": "test_value"})
