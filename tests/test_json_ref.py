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
import os
from pyLibrary import jsons
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
        self.assertEqual(doc.relative_object_doc, {"key":"new value", "another_key":"another value"})

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
