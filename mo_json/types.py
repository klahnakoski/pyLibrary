# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import re
from datetime import datetime, date
from decimal import Decimal

from mo_dots import split_field, NullType, is_many, is_data, concat_field
from mo_future import text, none_type, PY2, long, items, first
from mo_logs import Log
from mo_times import Date


def to_jx_type(value):
    if isinstance(value, JxType):
        return value
    try:
        return _type_to_json_type[value]
    except Exception:
        return T_JSON


class JxType(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, JxType):
                setattr(self, k, v)
            else:
                Log.error("Not allowed")

    def __or__(self, other):
        other = to_jx_type(other)
        if self is T_IS_NULL:
            return other

        sd = self.__dict__.copy()
        od = other.__dict__

        dirty = False
        for k, ov in od.items():
            sv = sd.get(k)
            if sv is ov:
                continue
            if sv is None:
                if k in T_NUMBER_TYPES.__dict__ and sd.get(_N):
                    continue
                elif k is _N and any(
                    sd.get(kk) for kk in T_NUMBER_TYPES.__dict__.keys()
                ):
                    for kk in T_NUMBER_TYPES.__dict__.keys():
                        try:
                            del sd[kk]
                        except Exception as cause:
                            pass
                    sd[k] = T_NUMBER.__dict__[k]
                    dirty = True
                    continue
                sd[k] = ov
                dirty = True
                continue
            if isinstance(sv, JxType) and isinstance(ov, JxType):
                new_value = sv | ov
                if new_value is sv:
                    continue
                sd[k] = new_value
                dirty = True
                continue

            Log.error("Not expected")

        if not dirty:
            return self

        output = _new(JxType)
        output.__dict__ = sd
        return output

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.keys())))

    def leaves(self):
        if self in T_PRIMITIVE:
            yield ".", self
        else:
            for k, v in self.__dict__.items():
                for p, t in v.leaves():
                    yield concat_field(k, p), t

    def __contains__(self, item):
        if not isinstance(item, JxType):
            return False
        sd = self.__dict__
        od = item.__dict__
        for k, ov in od.items():
            sv = sd.get(k)
            if sv is ARRAY:
                continue
            if sv != ov:
                return False
        return True

    def __eq__(self, other):
        if not isinstance(other, JxType):
            return False

        if self is T_INTEGER or self is T_NUMBER:
            if other is T_INTEGER or other is T_NUMBER:
                return True

        # DETECT DIFFERENCE BY ONLY NAME DEPTH
        sd = base_type(self).__dict__
        od = base_type(other).__dict__

        if len(sd) != len(od):
            return False

        try:
            for k, sv in sd.items():
                ov = od.get(k)
                if sv != ov:
                    return False
            return True
        except Exception as cause:
            sd = self.__dict__
            od = other.__dict__

            # DETECT DIFFERENCE BY ONLY NAME DEPTH
            sd = base_type(sd)
            od = base_type(od)

            Log.error("not expected", cause)

    def __radd__(self, path):
        """
        RETURN self AT THE END OF path
        :param path
        """
        acc = self
        for step in reversed(split_field(path)):
            if IS_PRIMITIVE_KEY.match(step):
                continue
            acc = JxType(**{step: acc})
        return acc

    def __data__(self):
        return {
            k: v.__data__() if isinstance(v, JxType) else str(v)
            for k, v in self.__dict__.items()
        }

    def __str__(self):
        return str(self.__data__())

    def __repr__(self):
        return "JxType(**"+str(self.__data__())+")"


def base_type(type_):
    """
    TYPES OFTEN COME WITH SIMPLE NAMES THAT GET IN THE WAY OF THE "BASE TYPE"
    THIS WILL STRIP EXTRANEOUS NAMES, RETURNING THE MOST BASIC TYPE
    EITHER A PRIMITIVE, OR A STRUCTURE

    USE THIS WHEN MANIPULATING FUNCTIONS THAT ACT ON VALUES, NOT STRUCTURES
    EXAMPLE: {"a": {"~n~": number}} REPRESENTS BOTH A STRUCTURE {"a": 1} AND A NUMBER
    """
    d = type_.__dict__
    ld = len(d)
    while ld == 1:
        n, t = first(d.items())
        if IS_PRIMITIVE_KEY.match(n):
            return type_
        if t in (ARRAY, JSON):
            return type_
        type_ = t
        d = t.__dict__
        ld = len(d)
    return type_


def union_type(*types):
    if len(types) == 1 and is_many(types[0]):
        Log.error("expecting many parameters")
    output = T_IS_NULL

    for t in types:
        output |= t
    return output


def array_type(item_type):
    return _primitive(_A, item_type)


_new = object.__new__


def _primitive(name, value):
    output = _new(JxType)
    setattr(output, name, value)
    return output


IS_NULL = "0"
BOOLEAN = "boolean"
INTEGER = "integer"
NUMBER = "number"
TIME = "time"
INTERVAL = "interval"
STRING = "string"
OBJECT = "object"
ARRAY = "nested"
EXISTS = "exists"
JSON = "any json"

ALL_TYPES = {
    IS_NULL: IS_NULL,
    BOOLEAN: BOOLEAN,
    INTEGER: INTEGER,
    NUMBER: NUMBER,
    TIME: TIME,
    INTERVAL: INTERVAL,
    STRING: STRING,
    OBJECT: OBJECT,
    ARRAY: ARRAY,
    EXISTS: EXISTS,
}
JSON_TYPES = (BOOLEAN, INTEGER, NUMBER, STRING, OBJECT)
NUMBER_TYPES = (INTEGER, NUMBER, TIME, INTERVAL)
PRIMITIVE = (EXISTS, BOOLEAN, INTEGER, NUMBER, TIME, INTERVAL, STRING)
INTERNAL = (EXISTS, OBJECT, ARRAY)
STRUCT = (OBJECT, ARRAY)

_B, _I, _N, _T, _D, _S, _A, _J = "~b~", "~i~", "~n~", "~t~", "~d~", "~s~", "~a~", "~j~"
IS_PRIMITIVE_KEY = re.compile(r"^~[bintds]~$")

T_IS_NULL = _new(JxType)
T_BOOLEAN = _primitive(_B, BOOLEAN)
T_INTEGER = _primitive(_I, INTEGER)
T_NUMBER = _primitive(_N, NUMBER)
T_TIME = _primitive(_T, TIME)
T_INTERVAL = _primitive(_D, INTERVAL)  # d FOR DELTA
T_TEXT = _primitive(_S, STRING)
T_ARRAY = _primitive(_A, ARRAY)
T_JSON = _primitive(_J, JSON)

T_PRIMITIVE = _new(JxType)
T_PRIMITIVE.__dict__ = [
    (x, x.update(d))[0]
    for x in [{}]
    for d in [
        T_BOOLEAN.__dict__,
        T_INTEGER.__dict__,
        T_NUMBER.__dict__,
        T_TIME.__dict__,
        T_INTERVAL.__dict__,
        T_TEXT.__dict__,
    ]
][0]
T_NUMBER_TYPES = _new(JxType)
T_NUMBER_TYPES.__dict__ = [
    (x, x.update(d))[0]
    for x in [{}]
    for d in [
        T_INTEGER.__dict__,
        T_NUMBER.__dict__,
        T_TIME.__dict__,
        T_INTERVAL.__dict__,
    ]
][0]

_type_to_json_type = {
    IS_NULL: T_IS_NULL,
    BOOLEAN: T_BOOLEAN,
    INTEGER: T_INTERVAL,
    NUMBER: T_NUMBER,
    TIME: T_TIME,
    INTERVAL: T_INTERVAL,
    STRING: T_TEXT,
    ARRAY: T_ARRAY,
}


def value_to_json_type(value):
    if is_many(value):
        return _primitive(_A, union_type(*(value_to_json_type(v) for v in value)))
    elif is_data(value):
        return JxType(**{k: value_to_json_type(v) for k, v in value.items()})
    else:
        return _python_type_to_jx_type[value.__class__]


def python_type_to_jx_type(type):
    return _python_type_to_jx_type[type]


_jx_type_to_json_type = {
    T_IS_NULL: IS_NULL,
    T_BOOLEAN: BOOLEAN,
    T_INTEGER: NUMBER,
    T_NUMBER: NUMBER,
    T_TIME: NUMBER,
    T_INTERVAL: NUMBER,
    T_TEXT: STRING,
    T_ARRAY: ARRAY,
    T_JSON: OBJECT,
}


def jx_type_to_json_type(jx_type):
    return _jx_type_to_json_type.get(base_type(jx_type))


_python_type_to_jx_type = {
    int: T_INTEGER,
    text: T_TEXT,
    float: T_NUMBER,
    Decimal: T_NUMBER,
    bool: T_BOOLEAN,
    NullType: T_IS_NULL,
    none_type: T_IS_NULL,
    Date: T_TIME,
    datetime: T_TIME,
    date: T_TIME,
}

if PY2:
    _python_type_to_jx_type[str] = T_TEXT
    _python_type_to_jx_type[long] = T_INTEGER


for k, v in items(_python_type_to_jx_type):
    _python_type_to_jx_type[k.__name__] = v

jx_type_to_key = {
    T_IS_NULL: _J,
    T_BOOLEAN: _B,
    T_INTEGER: _I,
    T_NUMBER: _N,
    T_TIME: _T,
    T_INTERVAL: _D,
    T_TEXT: _S,
    T_ARRAY: _A,
}

python_type_to_jx_type_key = {
    bool: _B,
    int: _I,
    float: _N,
    Decimal: _N,
    Date: _T,
    datetime: _T,
    date: _T,
    text: _S,
    NullType: _J,
    none_type: _J,
    list: _A,
    set: _A,
}

