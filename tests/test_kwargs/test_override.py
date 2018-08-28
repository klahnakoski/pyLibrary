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

from collections import Mapping

from mo_dots import unwrap
from mo_testing.fuzzytestcase import FuzzyTestCase

from mo_kwargs import override

kw = {"required": 1, "optional": 2}


class TestOverride(FuzzyTestCase):

    def test_basic(self):
        result = basic(required=0)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["required"], 0)
        self.assertEqual(result["optional"], 3)

    def test_basic_w_kwargs(self):
        result = basic(kwargs=kw)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["required"], 1)
        self.assertEqual(result["optional"], 2)

    def test_basic_w_override(self):
        result = basic(required=0, kwargs=kw)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["required"], 0)
        self.assertEqual(result["optional"], 2)

    def test_basic_w_option(self):
        result = basic(optional=3, kwargs=kw)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["required"], 1)
        self.assertEqual(result["optional"], 3)

    def test_no_param_args(self):
        result = no_param(kw)
        self.assertIsInstance(result, Mapping)
        self.assertEqual(len(result.keys()), 0)

    def test_no_param_kwargs(self):
        result = no_param(kwargs=kw)
        self.assertIsInstance(result, Mapping)
        self.assertEqual(len(result.keys()), 0)

    def test_nothing_w_nothing(self):
        result = nothing()
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result["kwargs"]), 1)

    def test_nothing_w_require(self):
        result = nothing(required=3)
        self.assertEqual(result, {"required": 3})

    def test_nothing_w_optional(self):
        result = nothing(optional=3)
        self.assertEqual(result, {"optional": 3})

    def test_nothing_w_both(self):
        result = nothing(required=3, optional=3)
        self.assertEqual(result, {"required": 3, "optional": 3})

    def test_nothing_w_nothing_and_kwargs(self):
        result = nothing(kwargs=kw)
        self.assertEqual(result, kw)

    def test_nothing_w_require_and_kwargs(self):
        result = nothing(required=3, kwargs=kw)
        self.assertEqual(result, {"required": 3})

    def test_nothing_w_optional_and_kwargs(self):
        result = nothing(optional=3, kwargs=kw)
        self.assertEqual(result, {"optional": 3})

    def test_nothing_w_both_and_kwargs(self):
        result = nothing(required=3, optional=3, kwargs=kw)
        self.assertEqual(result, {"required": 3, "optional": 3})

    def test_required_w_nothing(self):
        self.assertRaises(Exception, required)

    def test_required_w_require(self):
        result = required(required=3)
        self.assertEqual(result, {"required": 3})

    def test_required_w_optional(self):
        self.assertRaises(Exception, required, optional=3)

    def test_required_w_both(self):
        result = required(required=3, optional=3)
        self.assertEqual(result, {"required": 3, "optional": 3})

    def test_required_w_kwargs(self):
        result = required(kwargs=kw)
        self.assertEqual(result, kw)

    def test_required_w_default_kwargs(self):
        result = required(kw)
        self.assertEqual(result, kw)

    def test_required_w_require_and_kwargs(self):
        result = required(required=3, kwargs=kw)
        self.assertEqual(result, {"required": 3, "optional":2, "kwargs":{}})

    def test_required_w_optional_and_kwargs(self):
        result = required(optional=3, kwargs=kw)
        self.assertEqual(result, {"optional": 3})

    def test_required_w_both_and_kwargs(self):
        result = required(required=3, optional=3, kwargs=kw)
        self.assertEqual(result, {"required": 3, "optional":3, "kwargs":{}})

    def test_kwargs_w_nothing(self):
        result = kwargs()
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["kwargs_"]), 0)
        self.assertEqual(len(result["kwargs"]), 1)
        self.assertEqual(len(result["kwargs"]["kwargs"]), 1)

    def test_kwargs_w_require(self):
        result = kwargs(required=3)
        self.assertEqual(result, {"kwargs": {"required": 3}})

    def test_kwargs_w_optional(self):
        result = kwargs(optional=2)
        self.assertEqual(len(result["kwargs_"]), 0)
        self.assertEqual(len(result["kwargs"]), 2)
        self.assertEqual(result["kwargs"]["optional"], 2)

    def test_kwargs_w_both(self):
        result = kwargs(required=1, optional=2)
        self.assertEqual(result["kwargs"], kw)

    def test_kwargs_w_required_and_kwargs(self):
        result = kwargs(kwargs=kw)
        self.assertEqual(result, {"kwargs": {"required": 1, "optional": 2}})

    def test_kwargs_w_require_and_kwargs(self):
        result = kwargs(required=3, kwargs=kw)
        self.assertEqual(result, {"kwargs":{"required": 3}})

    def test_kwargs_w_optional_and_kwargs(self):
        result = kwargs(optional=2, kwargs=kw)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["kwargs"]), 3)
        self.assertEqual(result["kwargs"]["optional"], 2)
        self.assertEqual(result["kwargs"]["required"], 1)

    def test_kwargs_w_both_and_kwargs(self):
        result = kwargs(required=1, optional=2, kwargs=kw)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["kwargs_"]), 0)
        self.assertEqual(len(result["kwargs"]), 3)
        self.assertEqual(len(result["kwargs"]["kwargs"]), 3)

    def test_object_not_enough_parameters(self):
        self.assertRaises('Expecting parameter ["self", "required"], given ["optional", "kwargs"]', lambda: TestObject({}))

    def test_object(self):
        result = TestObject(kw)
        self.assertEqual(result.required, 1)
        self.assertEqual(result.optional, 2)
        self.assertEqual(result.kwargs["required"], 1)
        self.assertEqual(result.kwargs["optional"], 2)

    def test_object_w_kwargs(self):
        result = TestObject(kwargs=kw)
        self.assertEqual(result.required, 1)
        self.assertEqual(result.optional, 2)
        self.assertEqual(result.kwargs["required"], 1)
        self.assertEqual(result.kwargs["optional"], 2)

    def test_object_w_required(self):
        result = TestObject(required=0, kwargs=kw)
        self.assertEqual(result.required, 0)
        self.assertEqual(result.optional, 2)
        self.assertEqual(result.kwargs["required"], 0)
        self.assertEqual(result.kwargs["optional"], 2)

    def test_object_w_optional(self):
        result = TestObject(optional=3, kwargs=kw)
        self.assertEqual(result.required, 1)
        self.assertEqual(result.optional, 3)
        self.assertEqual(result.kwargs["required"], 1)
        self.assertEqual(result.kwargs["optional"], 3)

    def test_object_nothing_w_nothing(self):
        result = TestObject(required=0).nothing()
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result["kwargs"]), 1)

    def test_object_nothing_w_require(self):
        result = TestObject(required=0).nothing(required=3)
        self.assertEqual(result, {"required": 3})

    def test_object_nothing_w_optional(self):
        result = TestObject(required=0).nothing(optional=3)
        self.assertEqual(result, {"optional": 3})

    def test_object_nothing_w_both(self):
        result = TestObject(required=0).nothing(required=3, optional=3)
        self.assertEqual(result, {"required": 3, "optional": 3})

    def test_object_nothing_w_nothing_and_kwargs(self):
        result = TestObject(required=0).nothing(kwargs=kw)
        self.assertEqual(result, kw)

    def test_object_nothing_w_require_and_kwargs(self):
        result = TestObject(required=0).nothing(required=3, kwargs=kw)
        self.assertEqual(result, {"required": 3})

    def test_object_nothing_w_optional_and_kwargs(self):
        result = TestObject(required=0).nothing(optional=3, kwargs=kw)
        self.assertEqual(result, {"optional": 3})

    def test_object_nothing_w_both_and_kwargs(self):
        result = TestObject(required=0).nothing(required=3, optional=3, kwargs=kw)
        self.assertEqual(result, {"required": 3, "optional": 3})

    def test_object_required_w_nothing(self):
        self.assertRaises(Exception, required)

    def test_object_required_w_require(self):
        result = TestObject(required=0).required_(required=3)
        self.assertEqual(result, {"required": 3})

    def test_object_required_w_optional(self):
        self.assertRaises(Exception, required, optional=3)

    def test_object_required_w_both(self):
        result = TestObject(required=0).required_(required=3, optional=3)
        self.assertEqual(result, {"required": 3, "optional": 3})

    def test_object_required_w_kwargs(self):
        result = TestObject(required=0).required_(kwargs=kw)
        self.assertEqual(result, kw)

    def test_object_required_w_default_kwargs(self):
        result = TestObject(required=0).required_(kw)
        self.assertEqual(result, kw)

    def test_object_required_w_require_and_kwargs(self):
        result = TestObject(required=0).required_(required=3, kwargs=kw)
        self.assertEqual(result, {"required": 3, "optional":2, "kwargs":{}})

    def test_object_required_w_optional_and_kwargs(self):
        result = TestObject(required=0).required_(optional=3, kwargs=kw)
        self.assertEqual(result, {"optional": 3})

    def test_object_required_w_both_and_kwargs(self):
        result = TestObject(required=0).required_(required=3, optional=3, kwargs=kw)
        self.assertEqual(result, {"required": 3, "optional":3, "kwargs":{}})

    def test_object_kwargs_w_nothing(self):
        result = TestObject(required=0).kwargs_()
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["kwargs_"]), 0)
        self.assertEqual(len(result["kwargs"]), 1)
        self.assertEqual(len(result["kwargs"]["kwargs"]), 1)

    def test_object_kwargs_w_require(self):
        result = TestObject(required=0).kwargs_(required=3)
        self.assertEqual(result, {"kwargs": {"required": 3}})

    def test_object_kwargs_w_optional(self):
        result = TestObject(required=0).kwargs_(optional=2)
        self.assertEqual(len(result["kwargs_"]), 0)
        self.assertEqual(len(result["kwargs"]), 2)
        self.assertEqual(result["kwargs"]["optional"], 2)

    def test_object_kwargs_w_both(self):
        result = TestObject(required=0).kwargs_(required=1, optional=2)
        self.assertEqual(result["kwargs"], kw)

    def test_object_kwargs_w_required_and_kwargs(self):
        result = TestObject(required=0).kwargs_(kwargs=kw)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["kwargs"]), 3)
        self.assertIs(unwrap(result["kwargs"]), unwrap(result["kwargs"]["kwargs"]))
        self.assertEqual(len(result["kwargs_"]), 0)
        self.assertEqual(result, {"kwargs": {"required": 1, "optional": 2}})

    def test_object_kwargs_w_require_and_kwargs(self):
        result = TestObject(required=0).kwargs_(required=3, kwargs=kw)
        self.assertEqual(result, {"kwargs":{"required": 3}})

    def test_object_kwargs_w_optional_and_kwargs(self):
        result = TestObject(required=0).kwargs_(optional=2, kwargs=kw)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["kwargs"]), 3)
        self.assertIs(unwrap(result["kwargs"]), unwrap(result["kwargs"]["kwargs"]))
        self.assertEqual(len(result["kwargs_"]), 0)
        self.assertEqual(result, {"kwargs": {"optional": 2}})

    def test_object_kwargs_w_both_and_kwargs(self):
        result = TestObject(required=0).kwargs_(required=1, optional=2, kwargs=kw)
        self.assertEqual(len(result), 2)
        self.assertEqual(len(result["kwargs_"]), 0)
        self.assertEqual(len(result["kwargs"]), 3)
        self.assertEqual(len(result["kwargs"]["kwargs"]), 3)


@override
def basic(required, optional=3):
    return {"required": required, "optional": optional}


@override
def nothing(kwargs=None):
    return kwargs


@override
def no_param(*args, **kwargs):
    return kwargs


@override
def required(required, optional=3, kwargs=None):
    return {"required": required, "optional": optional, "kwargs": kwargs}


@override
def kwargs(kwargs=None, **kwargs_):
    return {"kwargs": kwargs, "kwargs_": kwargs_}


class TestObject(object):

    @override
    def __init__(self, required, optional=3, kwargs=None):
        self.required = required
        self.optional = optional
        self.kwargs = kwargs

    @override
    def nothing(self, kwargs=None):
        return kwargs

    @override
    def required_(self, required, optional=3, kwargs=None):
        return {"required": required, "optional": optional, "kwargs": kwargs}

    @override
    def kwargs_(self, kwargs=None, **kwargs_):
        return {"kwargs_": kwargs_, "kwargs": kwargs}

