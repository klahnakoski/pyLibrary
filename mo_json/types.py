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
from math import isnan

from mo_dots import split_field, NullType, is_many, is_data, concat_field, is_sequence
from mo_future import text, none_type, items, first, POS_INF
from mo_logs import Log
from mo_times import Date


def to_jx_type(value):
    if isinstance(value, JxType):
        return value
    try:
        return _json_type_to_jx_type[value]
    except Exception:
        return JX_ANY


class JxType(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __or__(self, other):
        other = to_jx_type(other)
        if self is JX_IS_NULL:
            return other
        if self is JX_ANY:
            return self

        sd = self.__dict__.copy()
        od = other.__dict__

        dirty = False
        for k, ov in od.items():
            sv = sd.get(k)
            if sv is ov:
                continue
            if sv is None:
                if k in JX_NUMBER_TYPES.__dict__ and sd.get(NUMBER_KEY):
                    continue
                elif k is NUMBER_KEY and any(sd.get(kk) for kk in JX_NUMBER_TYPES.__dict__.keys()):
                    for kk in JX_NUMBER_TYPES.__dict__.keys():
                        try:
                            del sd[kk]
                        except Exception as cause:
                            pass
                    sd[k] = JX_NUMBER.__dict__[k]
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

    def __getitem__(self, item):
        if self is JX_ANY:
            return self
        return self.__dict__.get(item)

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.keys())))

    def leaves(self):
        if self in JX_PRIMITIVE:
            yield ".", self
        else:
            for k, v in self.__dict__.items():
                for p, t in v.leaves():
                    yield concat_field(k, p), t

    def __contains__(self, item):
        if isinstance(item, str):
            return item in self.__dict__
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

    def __ne__(self, other):
        if self is JX_ANY and other is ARRAY:
            return False
        return not self == other

    def __eq__(self, other):
        if other is ARRAY and hasattr(self, ARRAY_KEY):
            # SHALLOW CHECK IF THIS IS AN ARRAY
            return True

        if not isinstance(other, JxType):
            return False

        if self is JX_INTEGER or self is JX_NUMBER:
            if other is JX_INTEGER or other is JX_NUMBER:
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
        return {k: v.__data__() if isinstance(v, JxType) else str(v) for k, v in self.__dict__.items()}

    def __str__(self):
        return str(self.__data__())

    def __repr__(self):
        return "JxType(**" + str(self.__data__()) + ")"


def array_of(type_):
    return JxType(**{ARRAY_KEY: type_})


def member_type(type_):
    """
    RETURN THE MEMBER TYPE, IF AN ARRAY
    """
    if type_ == ARRAY:
        return getattr(type_, ARRAY_KEY)
    else:
        return type_


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
    output = JX_IS_NULL

    for t in types:
        output |= t
    return output


def array_type(item_type):
    return _primitive(ARRAY_KEY, item_type)


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

BOOLEAN_KEY, INTEGER_KEY, NUMBER_KEY, TIME_KEY, DURATION_KEY, STRING_KEY, ARRAY_KEY, EXISTS_KEY, JSON_KEY = "~b~", "~i~", "~n~", "~t~", "~d~", "~s~", "~a~", "~e~", "~j~"
IS_PRIMITIVE_KEY = re.compile(r"^~[bintds]~$")
IS_TYPE_KEY = re.compile(r"^~[bintdsaje]~$")

JX_IS_NULL = _new(JxType)
JX_BOOLEAN = _primitive(BOOLEAN_KEY, BOOLEAN)
JX_INTEGER = _primitive(INTEGER_KEY, INTEGER)
JX_NUMBER = _primitive(NUMBER_KEY, NUMBER)
JX_TIME = _primitive(TIME_KEY, TIME)
JX_INTERVAL = _primitive(DURATION_KEY, INTERVAL)  # d FOR DELTA
JX_TEXT = _primitive(STRING_KEY, STRING)
JX_ARRAY = _primitive(ARRAY_KEY, ARRAY)
JX_ANY = _primitive(JSON_KEY, JSON)

JX_PRIMITIVE = _new(JxType)
JX_PRIMITIVE.__dict__ = [
    (x, x.update(d))[0]
    for x in [{}]
    for d in [
        JX_BOOLEAN.__dict__,
        JX_INTEGER.__dict__,
        JX_NUMBER.__dict__,
        JX_TIME.__dict__,
        JX_INTERVAL.__dict__,
        JX_TEXT.__dict__,
    ]
][0]
JX_NUMBER_TYPES = _new(JxType)
JX_NUMBER_TYPES.__dict__ = [
    (x, x.update(d))[0]
    for x in [{}]
    for d in [JX_INTEGER.__dict__, JX_NUMBER.__dict__, JX_TIME.__dict__, JX_INTERVAL.__dict__]
][0]

_json_type_to_jx_type = {
    IS_NULL: JX_IS_NULL,
    BOOLEAN: JX_BOOLEAN,
    INTEGER: JX_INTERVAL,
    NUMBER: JX_NUMBER,
    TIME: JX_TIME,
    INTERVAL: JX_INTERVAL,
    STRING: JX_TEXT,
    ARRAY: JX_ARRAY,
}


def value_to_json_type(v):
    if v == None:
        return None
    elif isinstance(v, bool):
        return BOOLEAN
    elif isinstance(v, str):
        return STRING
    elif is_data(v):
        return OBJECT
    elif isinstance(v, float):
        if isnan(v) or abs(v) == POS_INF:
            return None
        return NUMBER
    elif isinstance(v, (int, Date)):
        return NUMBER
    elif is_sequence(v):
        return ARRAY
    return None


def value_to_jx_type(value):
    if is_many(value):
        return _primitive(ARRAY_KEY, union_type(*(value_to_json_type(v) for v in value)))
    elif is_data(value):
        return JxType(**{k: value_to_json_type(v) for k, v in value.items()})
    else:
        return _python_type_to_jx_type[value.__class__]


def python_type_to_jx_type(type):
    return _python_type_to_jx_type.get(type, JX_ANY)


_jx_type_to_json_type = {
    JX_IS_NULL: IS_NULL,
    JX_BOOLEAN: BOOLEAN,
    JX_INTEGER: NUMBER,
    JX_NUMBER: NUMBER,
    JX_TIME: NUMBER,
    JX_INTERVAL: NUMBER,
    JX_TEXT: STRING,
    JX_ARRAY: ARRAY,
    JX_ANY: OBJECT,
}


def jx_type_to_json_type(jx_type):
    return _jx_type_to_json_type.get(base_type(jx_type))


_python_type_to_jx_type = {
    int: JX_INTEGER,
    text: JX_TEXT,
    float: JX_NUMBER,
    Decimal: JX_NUMBER,
    bool: JX_BOOLEAN,
    NullType: JX_IS_NULL,
    none_type: JX_IS_NULL,
    Date: JX_TIME,
    datetime: JX_TIME,
    date: JX_TIME,
}

for k, v in items(_python_type_to_jx_type):
    _python_type_to_jx_type[k.__name__] = v

jx_type_to_key = {
    JX_IS_NULL: JSON_KEY,
    JX_BOOLEAN: BOOLEAN_KEY,
    JX_INTEGER: INTEGER_KEY,
    JX_NUMBER: NUMBER_KEY,
    JX_TIME: TIME_KEY,
    JX_INTERVAL: DURATION_KEY,
    JX_TEXT: STRING_KEY,
    JX_ARRAY: ARRAY_KEY,
}

python_type_to_jx_type_key = {
    bool: BOOLEAN_KEY,
    int: INTEGER_KEY,
    float: NUMBER_KEY,
    Decimal: NUMBER_KEY,
    Date: TIME_KEY,
    datetime: TIME_KEY,
    date: TIME_KEY,
    text: STRING_KEY,
    NullType: JSON_KEY,
    none_type: JSON_KEY,
    list: ARRAY_KEY,
    set: ARRAY_KEY,
}
