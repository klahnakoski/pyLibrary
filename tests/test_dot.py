# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from UserDict import UserDict
from collections import Mapping

from pyLibrary.collections import MAX
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import wrap, Dict, Null, set_default, unwrap
from pyLibrary.dot.objects import dictwrap
from pyLibrary.meta import DataClass
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase


class TestDot(FuzzyTestCase):

    def test_userdict(self):
        def show_kwargs(**kwargs):
            return kwargs

        a = UserDict(a=1, b=2)
        d = show_kwargs(**a)
        self.assertAlmostEqual(d, {"a":1, "b":2})

    def test__userdict(self):
        def show_kwargs(**kwargs):
            return kwargs

        a = _UserDict()
        a.data["a"] = 1
        a.data["b"] = 2
        d = show_kwargs(**a)
        self.assertAlmostEqual(d, {"a":1, "b":2})

    def test_dict_args(self):
        def show_kwargs(**kwargs):
            return kwargs

        a = Dict()
        a["a"] = 1
        a["b"] = 2
        d = show_kwargs(**a)
        self.assertAlmostEqual(d, {"a": 1, "b": 2})

    def test_is_mapping(self):
        self.assertTrue(isinstance(Dict(), Mapping), "All Dict must be Mappings")

    def test_none(self):
        a = 0
        b = 0
        c = None
        d = None

        if a == b:
            pass
        else:
            Log.error("error")

        if c == d:
            pass
        else:
            Log.error("error")

        if a == c:
            Log.error("error")

        if d == b:
            Log.error("error")

        if not c:
            pass
        else:
            Log.error("error")


    def test_null(self):
        a = 0
        b = 0
        c = Null
        d = Null
        e = Dict()
        f = Dict()

        if a == b:
            pass
        else:
            Log.error("error")

        if c == d:
            pass
        else:
            Log.error("error")

        if a == c:
            Log.error("error")

        if d == b:
            Log.error("error")

        if c == None:
            pass
        else:
            Log.error("error")

        if not c:
            pass
        else:
            Log.error("error")

        if Null != Null:
            Log.error("error")

        if Null != None:
            Log.error("error")

        if None != Null:
            Log.error("error")

        if e.test != f.test:
            Log.error("error")

    def test_get_value(self):
        a = wrap({"a": 1, "b": {}})

        if a.a != 1:
            Log.error("error")
        if not isinstance(a.b, Mapping):
            Log.error("error")

    def test_get_class(self):
        a = wrap({})
        _type = a.__class__

        if _type is not Dict:
            Log.error("error")

    def test_int_null(self):
        a = Dict()
        value = a.b*1000
        assert value == Null

    def test_dot_self(self):
        a = Dict(b=42)
        assert a["."] == a
        assert a["."].b == 42

        a["."] = {"c": 42}
        assert a.c == 42
        assert a.b == None


    def test_list(self):
        if not []:
            pass
        else:
            Log.error("error")

        if []:
            Log.error("error")

        if not [0]:
            Log.error("error")


    def test_assign1(self):
        a = {}

        b = wrap(a)
        b.c = "test1"
        b.d.e = "test2"
        b.f.g.h = "test3"
        b.f.i = "test4"
        b.k["l.m.n"] = "test5"

        expected = {
            "c": "test1",
            "d": {
                "e": "test2"
            },
            "f": {
                "g": {
                    "h": "test3"
                },
                "i": "test4"
            },
            "k": {
                "l": {"m": {"n": "test5"}}
            }
        }
        self.assertEqual(a, expected)


    def test_assign2(self):
        a = {}

        b = wrap(a)
        b_c = b.c
        b.c.d = "test1"

        b_c.e = "test2"

        expected = {
            "c": {
                "d": "test1",
                "e": "test2"
            }
        }
        self.assertEqual(a, expected)

    def test_assign3(self):
        # IMPOTENT ASSIGNMENTS DO NOTHING
        a = {}
        b = wrap(a)

        b.c = None
        expected = {}
        self.assertEqual(a, expected)

        b.c.d = None
        expected = {}
        self.assertEqual(a, expected)

        b["c.d"] = None
        expected = {}
        self.assertEqual(a, expected)

        b.c.d.e = None
        expected = {}
        self.assertEqual(a, expected)

        b.c["d.e"] = None
        expected = {}
        self.assertEqual(a, expected)

    def test_assign4(self):
        # IMPOTENT ASSIGNMENTS DO NOTHING
        a = {"c": {"d": {}}}
        b = wrap(a)
        b.c.d = None
        expected = {"c": {}}
        self.assertEqual(a, expected)

        a = {"c": {"d": {}}}
        b = wrap(a)
        b.c = None
        expected = {}
        self.assertEqual(a, expected)


    def test_assign5(self):
        a = {}
        b = wrap(a)

        b.c["d\.e"].f = 2
        expected = {"c": {"d.e": {"f": 2}}}
        self.assertEqual(a, expected)


    def test_increment(self):
        a = {}
        b = wrap(a)
        b.c1.d += 1
        b.c2.e += "e"
        b.c3.f += ["f"]
        b["c\\.a"].d += 1

        self.assertEqual(a,  {"c1": {"d": 1}, "c2": {"e": "e"}, "c3": {"f": ["f"]}, "c.a": {"d": 1}})

        b.c1.d += 2
        b.c2.e += "f"
        b.c3.f += ["g"]
        b["c\\.a"].d += 3
        self.assertEqual(a,  {"c1": {"d": 3}, "c2": {"e": "ef"}, "c3": {"f": ["f", "g"]}, "c.a": {"d": 4}})

    def test_slicing(self):

        def diff(record, index, records):
            """
            WINDOW FUNCTIONS TAKE THE CURRENT record, THE index THAT RECORD HAS
            IN THE WINDOW, AND THE (SORTED) LIST OF ALL records
            """
            # COMPARE CURRENT VALUE TO MAX OF PAST 5, BUT NOT THE VERY LAST ONE
            try:
                return record - MAX(records[index - 6:index - 1:])
            except Exception, e:
                return None


        data1_list = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        result1 = [diff(r, i, data1_list) for i, r in enumerate(data1_list)]
        assert result1 == [-7, None, None, None, None, None, 2, 2, 2]  # WHAT IS EXPECTED, BUT NOT WHAT WE WANT

        data2_list = wrap(data1_list)
        result2 = [diff(r, i, data2_list) for i, r in enumerate(data2_list)]
        assert result2 == [None, None, 2, 2, 2, 2, 2, 2, 2]

    def test_delete1(self):
        a = wrap({"b": {"c": 1}})

        del a.b.c
        self.assertEqual({}, a)
        self.assertEqual(a, {})

        a = wrap({"b": {"c": 1}})

        a.b.c=None
        self.assertEqual({}, a)
        self.assertEqual(a, {})



    def test_delete2(self):
        a = wrap({"b": {"c": 1, "d": 2}})

        del a.b.c
        self.assertEqual({"b": {"d": 2}}, a)
        self.assertEqual(a, {"b": {"d": 2}})
        a = wrap({"b": {"c": 1, "d": 2}})

        a.b.c=None
        self.assertEqual({"b": {"d": 2}}, a)
        self.assertEqual(a, {"b": {"d": 2}})


    def test_object_wrap(self):
        d = Data()
        dd = dictwrap(d)

        self.assertEqual(dd["a"], 20)
        self.assertEqual(dd, {"a": 20, "b": 30})

    def test_deep_select(self):
        d = wrap([{"a": {"b": 1}}, {"a": {"b": 2}}])

        test = d.a.b
        self.assertEqual(test, [1, 2])

    def test_set_default(self):
        a = {"x": {"y": 1}}
        b = {"x": {"z": 2}}
        c = {}
        d = set_default(c, a, b)

        self.assertTrue(unwrap(d) is c, "expecting first parameter to be returned")
        self.assertEqual(d.x.y, 1, "expecting d to have attributes of a")
        self.assertEqual(d.x.z, 2, "expecting d to have attributes of b")

        self.assertEqual(wrap(a).x.z, None, "a should not have been altered")

    def test_Dict_of_Dict(self):
        value = {"a": 1}
        wrapped = Dict(Dict(value))
        self.assertTrue(value is unwrap(wrapped), "expecting identical object")


    def test_leaves_of_mappings(self):
        a = wrap({"a": _TestMapping()})
        a.a.a = {"a": 1}
        a.a.b = {"b": 2}

        leaves = wrap(dict(a.leaves()))
        self.assertEqual(a.a.a['a'], leaves["a\.a\.a"], "expecting 1")
        self.assertEqual(a.a.b['b'], leaves["a\.b\.b"], "expecting 2")




_TestMapping = DataClass("_TestMapping", ["a", "b"])







class _UserDict:
    """
    COPY OF UserDict
    """
    def __init__(self, **kwargs):
        self.data = {}
    def __getitem__(self, key):
        if key in self.data:
            return self.data[key]
        if hasattr(self.__class__, "__missing__"):
            return self.__class__.__missing__(self, key)
        raise KeyError(key)
    def keys(self):
        return self.data.keys()


class Data(object):

    def __init__(self):
        self.a = 20
        self.b = 30

    def __str__(self):
        return str(self.a)+str(self.b)
