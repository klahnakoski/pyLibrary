# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from collections import OrderedDict

from mo_dots import is_many, is_data, exists, is_missing
from mo_dots.datas import register_data

from mo_json import python_type_to_jx_type_key, IS_PRIMITIVE_KEY, ARRAY_KEY, EXISTS_KEY, NUMBER_KEY


def entype(value):
    """
    MAKE SURE VALUE IS TYPED
    """
    if isinstance(value, TypedObject):
        return value
    else:
        return TypedObject(value)


def entype_array(values):
    return {ARRAY_KEY: values}


class TypedObject(OrderedDict):
    """
    LAZY BOX FOR TYPED OBJECTS
    """
    __slots__ = ["_boxed_value"]

    def __init__(self, value):
        self._boxed_value = value

    def __getitem__(self, item):
        if item == NUMBER_KEY:
            if isinstance(self._boxed_value, (int, float)):
                return self._boxed_value
            return None
        elif item == ARRAY_KEY:
            if is_many(self._boxed_value):
                return [TypedObject(v) for v in self._boxed_value]
            return None
        elif IS_PRIMITIVE_KEY.match(item):
            expected = python_type_to_jx_type_key.get(type(self._boxed_value))
            if item == expected:
                return self._boxed_value
            return None
        elif item == EXISTS_KEY:
            if is_many(self._boxed_value):
                return len(self._boxed_value)
            elif exists(self._boxed_value):
                return 1
            return 0
        elif is_missing(self._boxed_value):
            return None
        else:
            try:
                return TypedObject(self._boxed_value[item])
            except KeyError:
                pass
            try:
                return TypedObject(getattr(self._boxed_value, item))
            except KeyError:
                pass
            return None

    def keys(self):
        if is_missing(self._boxed_value):
            return set()
        if is_data(self._boxed_value):
            return self._boxed_value.keys()
        type_key = python_type_to_jx_type_key.get(type(self._boxed_value))
        return set(type_key)

    def items(self):
        value = self._boxed_value
        if is_missing(value):
            return []
        if is_data(value):
            return [(k, TypedObject(v)) for k, v in value.items()]
        if is_many(value):
            return [(ARRAY_KEY, [TypedObject(v) for v in value])]
        type_key = python_type_to_jx_type_key.get(type(value))
        return [(type_key, value)]

    def __str__(self):
        return str(self._boxed_value)

    def __repr__(self):
        return repr(self._boxed_value)


register_data(TypedObject)
