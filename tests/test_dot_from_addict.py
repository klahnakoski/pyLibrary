# encoding: utf-8
#
# DEC 2016 - Altered tests to work with differing definitions
#
# SNAGGED FROM https://github.com/mewwts/addict/blob/62e8481a2a5c8520259809fc306698489975c9f8/test_addict.py WITH THE FOLLOWING LICENCE
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Mats Julian Olsen
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import unicode_literals

from collections import Mapping
from copy import copy, deepcopy
import json
import pickle
from unittest import skipIf

from pyLibrary import convert
from pyLibrary.dot import Dict, set_default, unwrap
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase

TEST_VAL = [1, 2, 3]
TEST_DICT = {'a': {'b': {'c': TEST_VAL}}}


class AddictTests(FuzzyTestCase):

    def test_set_one_level_item(self):
        some_dict = {'a': TEST_VAL}
        prop = Dict()
        prop['a'] = TEST_VAL
        self.assertEqual(prop, some_dict)

    def test_set_two_level_items(self):
        some_dict = {'a': {'b': TEST_VAL}}
        prop = Dict()
        prop['a']['b'] = TEST_VAL
        self.assertEqual(prop, some_dict)

    def test_set_three_level_items(self):
        prop = Dict()
        prop['a']['b']['c'] = TEST_VAL
        self.assertEqual(prop, TEST_DICT)

    def test_set_one_level_property(self):
        prop = Dict()
        prop.a = TEST_VAL
        self.assertEqual(prop, {'a': TEST_VAL})

    def test_set_two_level_properties(self):
        prop = Dict()
        prop.a.b = TEST_VAL
        self.assertEqual(prop, {'a': {'b': TEST_VAL}})

    def test_set_three_level_properties(self):
        prop = Dict()
        prop.a.b.c = TEST_VAL
        self.assertEqual(prop, TEST_DICT)

    def test_init_with_dict(self):
        self.assertEqual(TEST_DICT, Dict(TEST_DICT))

    def test_init_with_kws(self):
        prop = Dict(a=2, b={'a': 2}, c=[{'a': 2}])
        self.assertEqual(prop, {'a': 2, 'b': {'a': 2}, 'c': [{'a': 2}]})

    def test_init_with_list(self):
        prop = Dict([('0', 1), ('1', 2), ('2', 3)])
        self.assertEqual(prop, {'0': 1, '1': 2, '2': 3})

    def test_init_raises(self):
        def init():
            Dict(5)

        def init2():
            Dict('a')
        self.assertRaises(Exception, init)
        self.assertRaises(Exception, init2)

    def test_init_with_empty_stuff(self):
        a = Dict({})
        b = Dict([])
        self.assertEqual(a, {})
        self.assertEqual(b, {})

    def test_init_with_list_of_dicts(self):
        a = Dict({'a': [{'b': 2}]})
        self.assertIsInstance(a.a[0], Dict)
        self.assertEqual(a.a[0].b, 2)

    def test_getitem(self):
        prop = Dict(TEST_DICT)
        self.assertEqual(prop['a']['b']['c'], TEST_VAL)

    def test_empty_getitem(self):
        prop = Dict()
        prop.a.b.c
        self.assertEqual(prop, {})

    def test_getattr(self):
        prop = Dict(TEST_DICT)
        self.assertEqual(prop.a.b.c, TEST_VAL)

    def test_isinstance(self):
        self.assertTrue(isinstance(Dict(), Mapping))

    def test_str(self):
        prop = Dict(TEST_DICT)
        self.assertEqual(str(prop), str(TEST_DICT))

    def test_json(self):
        some_dict = TEST_DICT
        some_json = convert.value2json(some_dict)
        prop = Dict()
        prop.a.b.c = TEST_VAL
        prop_json = convert.value2json(prop)
        self.assertEqual(some_json, prop_json)

    def test_delitem(self):
        prop = Dict({'a': 2})
        del prop['a']
        self.assertEqual(prop, {})

    def test_delitem_nested(self):
        prop = Dict(deepcopy(TEST_DICT))
        del prop['a']['b']['c']
        self.assertEqual(prop, {'a': {'b': {}}})

    def test_delattr(self):
        prop = Dict({'a': 2})
        del prop.a
        self.assertEqual(prop, {})

    def test_delattr_nested(self):
        prop = Dict(deepcopy(TEST_DICT))
        del prop.a.b.c
        self.assertEqual(prop, {'a': {'b': {}}})

    def test_delitem_delattr(self):
        prop = Dict(deepcopy(TEST_DICT))
        del prop.a['b']
        self.assertEqual(prop, {'a': {}})

    def test_set_prop_invalid(self):
        prop = Dict()
        prop.keys = 2
        prop.items = 3

        self.assertEqual(prop, {'keys': 2, 'items': 3})

    def test_dir(self):
        key = 'a'
        prop = Dict({key: 1})
        dir_prop = dir(prop)

        dir_dict = dir(Dict)
        for d in dir_dict:
            self.assertTrue(d in dir_prop, d)

        self.assertTrue('__methods__' not in dir_prop)
        self.assertTrue('__members__' not in dir_prop)

    def test_dir_with_members(self):
        prop = Dict({'__members__': 1})
        dir(prop)
        self.assertTrue('__members__' in prop.keys())

    def test_unwrap(self):
        nested = {'a': [{'a': 0}, 2], 'b': {}, 'c': 2}
        prop = Dict(nested)
        regular = unwrap(prop)
        self.assertEqual(regular, prop)
        self.assertEqual(regular, nested)
        self.assertNotIsInstance(regular, Dict)

        def get_attr():
            regular.a = 2
        self.assertRaises(AttributeError, get_attr)

        def get_attr_deep():
            regular['a'][0].a = 1
        self.assertRaises(AttributeError, get_attr_deep)

    def test_to_dict_with_tuple(self):
        nested = {'a': ({'a': 0}, {2: 0})}
        prop = Dict(nested)
        regular = unwrap(prop)
        self.assertEqual(regular, prop)
        self.assertEqual(regular, nested)
        self.assertIsInstance(regular['a'], tuple)
        self.assertNotIsInstance(regular['a'][0], Dict)

    def test_update(self):
        old = Dict()
        old.child.a = 'a'
        old.child.b = 'b'
        old.foo = 'c'

        new = Dict()
        new.child.b = 'b2'
        new.child.c = 'c'
        new.foo.bar = True

        old = set_default({}, new, old)

        reference = {'foo': {'bar': True},
                     'child': {'a': 'a', 'c': 'c', 'b': 'b2'}}

        self.assertEqual(old, reference)

    def test_update_with_lists(self):
        org = Dict()
        org.a = [1, 2, {'a': 'superman'}]
        someother = Dict()
        someother.b = [{'b': 123}]
        org.update(someother)

        correct = {'a': [1, 2, {'a': 'superman'}],
                   'b': [{'b': 123}]}

        org.update(someother)
        self.assertEqual(org, correct)
        self.assertIsInstance(org.b[0], Mapping)

    def test_update_with_kws(self):
        org = Dict(one=1, two=2)
        someother = Dict(one=3)
        someother.update(one=1, two=2)
        self.assertEqual(org, someother)

    def test_update_with_args_and_kwargs(self):
        expected = {'a': 1, 'b': 2}
        org = Dict()
        org.update({'a': 3, 'b': 2}, a=1)
        self.assertEqual(org, expected)

    def test_update_with_multiple_args(self):
        org = Dict()
        def update():
            org.update({'a': 2}, {'a': 1})
        self.assertRaises(TypeError, update)

    def test_hook_in_constructor(self):
        a_dict = Dict(TEST_DICT)
        self.assertIsInstance(a_dict['a'], Dict)

    def test_copy(self):
        class MyMutableObject(object):

            def __init__(self):
                self.attribute = None

        foo = MyMutableObject()
        foo.attribute = True

        a = Dict()
        a.child.immutable = 42
        a.child.mutable = foo

        b = a.copy()

        # immutable object should not change
        b.child.immutable = 21
        self.assertEqual(a.child.immutable, 21)

        # mutable object should change
        b.child.mutable.attribute = False
        self.assertEqual(a.child.mutable.attribute, b.child.mutable.attribute)

        # changing child of b should not affect a
        b.child = "new stuff"
        self.assertTrue(isinstance(a.child, Dict))

    def test_deepcopy(self):
        class MyMutableObject(object):
            def __init__(self):
                self.attribute = None

        foo = MyMutableObject()
        foo.attribute = True

        a = Dict()
        a.child.immutable = 42
        a.child.mutable = foo

        b = deepcopy(a)

        # immutable object should not change
        b.child.immutable = 21
        self.assertEqual(a.child.immutable, 42)

        # mutable object should not change
        b.child.mutable.attribute = False
        self.assertTrue(a.child.mutable.attribute)

        # changing child of b should not affect a
        b.child = "new stuff"
        self.assertTrue(isinstance(a.child, Dict))

    def test_add_on_empty_dict(self):
        d = Dict()
        d.x.y += 1

        self.assertEqual(d.x.y, 1)

    def test_add_on_non_empty_dict(self):
        d = Dict()
        d.x.y = 'defined'

        def run():
            d.x += 1

        self.assertRaises(TypeError, run)

    def test_add_on_non_empty_value(self):
        d = Dict()
        d.x.y = 1
        d.x.y += 1

        self.assertEqual(d.x.y, 2)

    def test_add_on_unsupported_type(self):
        d = Dict()
        d.x.y = 'str'

        def test():
            d.x.y += 1

        self.assertRaises(TypeError, test)

    def test_init_from_zip(self):
        keys = ['a']
        values = [42]
        items = zip(keys, values)
        d = Dict(items)
        self.assertEqual(d.a, 42)


