# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with self file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import itertools
from numbers import Number

from mo_collections.unique_index import UniqueIndex
from mo_dots import (
    Data,
    FlatList,
    Null,
    coalesce,
    is_container,
    is_data,
    to_data,
    dict_to_data,
    list_to_data,
    from_data,
)
from mo_kwargs import override
from mo_logs import Log
from mo_math import MAX, MIN
from mo_times.dates import Date
from mo_times.durations import Duration

from jx_base.expressions import jx_expression, NULL, Expression
from jx_base.utils import enlist
from mo_json.types import (
    JxType,
    JX_NUMBER,
    JX_INTEGER,
    JX_TEXT,
    JX_TIME,
    JX_INTERVAL,
    python_type_to_jx_type,
)

# DOMAINS THAT HAVE ALGEBRAIC OPERATIONS DEFINED
ALGEBRAIC = {
    "time",
    "duration",
    "numeric",
    "count",
    "datetime",
}
# DOMAINS THAT HAVE A KNOWN NUMBER FOR PARTS AT QUERY TIME
KNOWN = {
    "set",
    "boolean",
    "duration",
    "time",
    "numeric",
}
# DIMENSIONS WITH CLEAR PARTS
PARTITION = {"uid", "set", "boolean"}


class Domain(object):
    __slots__ = [
        "name",
        "type",
        "element_type",
        "value",
        "key",
        "label",
        "end",
        "is_facet",
        "where",
        "dimension",
        "primitive",
        "limit",
    ]

    @override(kwargs="desc")
    def __new__(cls, type=None, desc=None):
        if cls == Domain:
            try:
                return object.__new__(name_to_type[type])
            except Exception as e:
                Log.error(
                    'Problem with {"domain":{"type":{{type|quote}}}}', type=type, cause=e,
                )
        else:
            return object.__new__(cls)

    @override(kwargs="desc")
    def __init__(
        self,
        name=None,
        value=None,
        key=None,
        label=None,
        end=None,
        is_facet=False,
        where=None,
        primitive=None,
        limit=NULL,
        desc=None,
    ):
        self._set_slots(self.__class__, desc)
        self.name = coalesce(name, type)
        if not isinstance(limit, Expression):
            self.limit = jx_expression(limit)
        self.dimension = Null

    def _set_slots(self, cls, data):
        """
        WHY ARE SLOTS NOT ACCESIBLE UNTIL WE ASSIGN TO THEM?
        """
        if hasattr(cls, "__slots__"):
            for s in cls.__slots__:
                self.__setattr__(s, data[s])
        for b in cls.__bases__:
            self._set_slots(b, data)

    def __copy__(self):
        return self.__class__(**self.__data__())

    def copy(self):
        return self.__class__(**self.__data__())

    def __data__(self):
        return dict_to_data({
            "name": self.name,
            "type": self.type,
            "value": self.value,
            "key": self.key,
            "is_facet": self.is_facet,
            "where": self.where,
            "dimension": self.dimension,
        })

    @property
    def __all_slots__(self):
        return self._all_slots(self.__class__)

    def _all_slots(self, cls):
        output = set(getattr(cls, "__slots__", []))
        for b in cls.__bases__:
            output |= self._all_slots(b)
        return output

    def getDomain(self):
        raise NotImplementedError()

    def verify_attributes_not_null(self, attribute_names):
        for name in attribute_names:
            if getattr(self, name) == None:
                Log.error(
                    "{{type}} domain expects a {{name|quote}} parameter", type=self.type, name=name,
                )


class UnitDomain(Domain):
    """
    REPRESENT A ZERO-DIMENSIONAL EDGE
    """

    def compare(self, a, b):
        return 0

    def getCanonicalPart(self, part):
        return 0

    def getPartByKey(self, key):
        return 0

    def getKey(self, part):
        return 0

    def getEnd(self, value):
        return 0


class ValueDomain(Domain):
    __slots__ = []

    def __init__(self, **desc):
        Domain.__init__(self, desc)

    def compare(self, a, b):
        return value_compare(a, b)

    def getCanonicalPart(self, part):
        return part

    def getPartByKey(self, key):
        return key

    def getKey(self, part):
        return part

    def getEnd(self, value):
        return value


class DefaultDomain(Domain):
    """
    DOMAIN IS A LIST OF OBJECTS, EACH WITH A value PROPERTY
    """

    __slots__ = ["partitions", "map", "limit", "sort"]

    @override(kwargs="desc")
    def __init__(
        self,
        type="default",
        name=None,
        value=None,
        key=None,
        label=None,
        end=None,
        is_facet=False,
        where=None,
        primitive=None,
        limit=None,
        desc=None,
    ):
        Domain.__init__(self, desc)
        self.partitions = FlatList()
        self.map = dict()
        self.map[None] = Null
        self.sort = 1

    def compare(self, a, b):
        return value_compare(a.value, b.value)

    def getCanonicalPart(self, part):
        return self.getPartByKey(part.value)

    def getPartByKey(self, key):
        canonical = self.map.get(key)
        if canonical:
            return canonical

        canonical = Data(name=key, value=key)

        self.partitions.append(canonical)
        self.map[key] = canonical
        return canonical

    def getKeyByIndex(self, index):
        return index

    def getIndexByKey(self, key):
        canonical = self.map.get(key)
        if canonical:
            return canonical.dataIndex

        index = len(self.partitions)
        canonical = Data(name=key, value=key, dataIndex=index)
        self.partitions.append(canonical)
        self.map[key] = canonical
        return index

    def getKey(self, part):
        return part.value

    def getEnd(self, part):
        return part.value

    def getLabel(self, part):
        return part.value

    def __data__(self):
        output = Domain.__data__(self)
        output.partitions = self.partitions
        output.limit = self.limit
        return output


class SimpleSetDomain(Domain):
    """
    DOMAIN IS A LIST OF OBJECTS, EACH WITH A value PROPERTY
    """

    __slots__ = [
        "partitions",  # LIST OF {name, value, dataIndex} dicts
        "map",  # MAP FROM value TO name
        "order",  # MAP FROM value TO dataIndex
    ]

    @override(kwargs="desc")
    def __init__(
        self,
        type="set",
        name=None,
        value=None,
        key=None,
        label=None,
        end=None,
        is_facet=False,
        where=None,
        primitive=None,
        limit=None,
        partitions=None,
        dimension=None,
        desc=None,
    ):
        Domain.__init__(self, desc)

        self.order = {}
        self.partitions = FlatList()
        self.primitive = True  # True IF DOMAIN IS A PRIMITIVE VALUE SET

        if isinstance(self.key, set):
            Log.error("problem")

        if not key and (len(partitions) == 0 or isinstance(partitions[0], (str, Number, tuple))):
            # ASSUME PARTS ARE STRINGS, CONVERT TO REAL PART OBJECTS
            self.key = "value"
            self.map = {}
            self.order[None] = len(partitions)
            for i, p in enumerate(partitions):
                part = {"value": p, "dataIndex": i}
                if isinstance(p, str):
                    part["name"] = p
                self.partitions.append(part)
                self.map[p] = part
                self.order[p] = i
                if isinstance(p, (int, float)):
                    text_part = str(float(p))  # ES CAN NOT HANDLE NUMERIC PARTS
                    self.map[text_part] = part
                    self.order[text_part] = i
            self.label = coalesce(self.label, "name")
            self.primitive = True
            return

        if partitions and dimension and dimension.fields and len(dimension.fields) > 1:
            self.key = key
            self.map = UniqueIndex(keys=dimension.fields)
        elif partitions and is_container(key):
            # TODO: key CAN BE MUCH LIKE A SELECT, WHICH UniqueIndex CAN NOT HANDLE
            self.key = key
            self.map = UniqueIndex(keys=key)
        elif partitions and is_data(partitions[0][key]):
            # LOOKS LIKE OBJECTS
            # sorted = partitions[key]

            self.key = key
            self.map = UniqueIndex(keys=key)
            self.order = {p[self.key]: p.dataIndex for p in partitions}
            self.partitions = partitions
        elif len(partitions) == 0:
            # CREATE AN EMPTY DOMAIN
            self.key = "value"
            self.map = {}
            self.order[None] = 0
            self.label = coalesce(self.label, "name")
            return
        elif key == None:
            if partitions and all(partitions.where):
                if not all(partitions.name):
                    Log.error("Expecting all partitions to have a name")
                self.key = "name"
                self.map = dict()
                self.map[None] = Null
                self.order[None] = len(partitions)
                for i, p in enumerate(partitions):
                    self.partitions.append({
                        "where": jx_expression(coalesce(p.where, p.esfilter)),
                        "name": p.name,
                        "dataIndex": i,
                    })
                    self.map[p.name] = p
                    self.order[p.name] = i
                return
            elif partitions and len(set(partitions.value) - {None}) == len(partitions):
                # TRY A COMMON KEY CALLED "value".  IT APPEARS UNIQUE
                self.key = "value"
                self.map = dict()
                self.map[None] = Null
                self.order[None] = len(partitions)
                for i, p in enumerate(partitions):
                    self.map[p[self.key]] = p
                    self.order[p[self.key]] = i
                self.primitive = False
            else:
                Log.error("Domains must have keys, or partitions")
        elif self.key:
            self.key = key
            self.map = dict()
            self.map[None] = Null
            self.order[None] = len(partitions)
            for i, p in enumerate(partitions):
                self.map[p[self.key]] = p
                self.order[p[self.key]] = i
            self.primitive = False
        else:
            Log.error("Can not hanldle")

        self.label = coalesce(self.label, "name")

        if hasattr(partitions, "__iter__"):
            self.partitions = to_data(list(partitions))
        else:
            Log.error("expecting a list of partitions")

    def compare(self, a, b):
        return value_compare(self.getKey(a), self.getKey(b))

    def getCanonicalPart(self, part):
        return self.getPartByKey(part.value)

    def getIndexByKey(self, key):
        try:
            output = self.order.get(key)
            if output is None:
                return len(self.partitions)
            return output
        except Exception as e:
            Log.error("problem", e)

    def getPartByKey(self, key):
        try:
            canonical = self.map.get(key)
            if not canonical:
                return Null
            return canonical
        except Exception as e:
            Log.error("problem", e)

    def getPartByIndex(self, index):
        return self.partitions[index]

    def getKeyByIndex(self, index):
        if index < 0 or index >= len(self.partitions):
            return None
        return self.partitions[index][self.key]

    def getKey(self, part):
        return part[self.key]

    def getEnd(self, part):
        if self.value:
            return part[self.value]
        else:
            return part

    def getLabel(self, part):
        return part[self.label]

    def __data__(self):
        output = Domain.__data__(self)
        output.partitions = self.partitions
        return output


class SetDomain(Domain):
    __slots__ = ["partitions", "map", "order"]

    def __init__(
        self,
        type="set",
        name=None,
        value=None,
        key=None,
        label=None,
        end=None,
        is_facet=False,
        where=None,
        primitive=None,
        limit=None,
        partitions=None,
        dimension=None,
        desc=None,
    ):

        Domain.__init__(self, desc)

        self.type = "set"
        self.order = {}
        self.partitions = FlatList()
        self.element_type = JxType(name=JX_TEXT, value=python_type_to_jx_type(partitions[0]), dataIndex=JX_INTEGER,)
        if isinstance(self.key, set):
            Log.error("problem")

        if isinstance(partitions[0], (int, float, str)):
            # ASSMUE PARTS ARE STRINGS, CONVERT TO REAL PART OBJECTS
            self.key = "value"
            self.order[None] = len(partitions)
            for i, p in enumerate(partitions):
                part = {"name": p, "value": p, "dataIndex": i}
                self.partitions.append(part)
                self.map[p] = part
                self.order[p] = i
        elif partitions and dimension.fields and len(dimension.fields) > 1:
            self.key = key
            self.map = UniqueIndex(keys=dimension.fields)
        elif partitions and is_container(key):
            # TODO: key CAN BE MUCH LIKE A SELECT, WHICH UniqueIndex CAN NOT HANDLE
            self.key = key
            self.map = UniqueIndex(keys=key)
        elif partitions and is_data(partitions[0][key]):
            self.key = key
            self.map = UniqueIndex(keys=key)
            # self.key = UNION(*set(d[key].keys()) for d in partitions)
            # self.map = UniqueIndex(keys=self.key)
        elif key == None:
            Log.error("Domains must have keys")
        elif self.key:
            self.key = key
            self.map = dict()
            self.map[None] = Null
            self.order[None] = len(partitions)
            for i, p in enumerate(partitions):
                self.map[p[self.key]] = p
                self.order[p[self.key]] = i
        elif all(p.esfilter for p in self.partitions):
            # EVERY PART HAS AN esfilter DEFINED, SO USE THEM
            for i, p in enumerate(self.partitions):
                p.dataIndex = i

        else:
            Log.error("Can not hanldle")

        self.label = coalesce(self.label, "name")

    def compare(self, a, b):
        return value_compare(self.getKey(a), self.getKey(b))

    def getCanonicalPart(self, part):
        return self.getPartByKey(part.value)

    def getIndexByKey(self, key):
        try:
            output = self.order.get(key)
            if output is None:
                return len(self.partitions)
            return output
        except Exception as e:
            Log.error("problem", e)

    def getPartByKey(self, key):
        try:
            canonical = self.map.get(key, None)
            if not canonical:
                return Null
            return canonical
        except Exception as e:
            Log.error("problem", e)

    def getKey(self, part):
        return part[self.key]

    def getKeyByIndex(self, index):
        return self.partitions[index][self.key]

    def getEnd(self, part):
        if self.value:
            return part[self.value]
        else:
            return part

    def getLabel(self, part):
        return part[self.label]

    def __data__(self):
        output = Domain.__data__(self)
        output.partitions = self.partitions
        return output


class TimeDomain(Domain):
    __slots__ = ["max", "min", "interval", "partitions", "sort"]

    @override(kwargs="desc")
    def __init__(
        self,
        type="time",
        name=None,
        value=None,
        key=None,
        label=None,
        end=None,
        is_facet=False,
        where=None,
        primitive=None,
        sort=None,
        limit=None,
        min=None,
        max=None,
        interval=None,
        partitions=None,
        desc=None,
    ):
        Domain.__init__(self, desc)
        self.min = Date(self.min)
        self.max = Date(self.max)
        self.interval = Duration(self.interval)
        self.sort = Null
        self.element_type = JxType(min=JX_TIME, max=JX_TIME, dataIndex=JX_INTEGER)

        if self.partitions:
            # IGNORE THE min, max, interval
            if not self.key:
                Log.error("Must have a key value")

            Log.error("not implemented yet")

            # VERIFY PARTITIONS DO NOT OVERLAP
            return

        self.verify_attributes_not_null(["min", "max", "interval"])
        self.key = "min"
        self.partitions = list_to_data([
            {"min": v, "max": v + self.interval, "dataIndex": i}
            for i, v in enumerate(Date.range(self.min, self.max, self.interval))
        ])

    def compare(self, a, b):
        return value_compare(a, b)

    def getCanonicalPart(self, part):
        return self.getPartByKey(part[self.key])

    def getIndexByKey(self, key):
        for p in self.partitions:
            if p.min <= key < p.max:
                return p.dataIndex
        return len(self.partitions)

    def getPartByKey(self, key):
        for p in self.partitions:
            if p.min <= key < p.max:
                return p
        return Null

    def getKey(self, part):
        return part[self.key]

    def getKeyByIndex(self, index):
        return self.partitions[index][self.key]

    def __data__(self):
        output = Domain.__data__(self)

        output.partitions = self.partitions
        output.min = self.min
        output.max = self.max
        output.interval = self.interval
        return output


class DurationDomain(Domain):
    __slots__ = ["max", "min", "interval", "partitions"]

    @override(kwargs="desc")
    def __init__(
        self,
        type="duration",
        name=None,
        value=None,
        key=None,
        label=None,
        end=None,
        is_facet=False,
        where=None,
        primitive=None,
        limit=None,
        min=None,
        max=None,
        interval=None,
        partitions=None,
        desc=None,
    ):
        self.element_type = JxType(min=JX_INTERVAL, max=JX_INTERVAL, dataIndex=JX_INTEGER)
        if partitions:
            # IGNORE THE min, max, interval
            if not key:
                Log.error("Must have a key value")

            Log.error("not implemented yet")

            # VERIFY PARTITIONS DO NOT OVERLAP
            return
        elif not all([min, max, interval]):
            Log.error("Can not handle missing parameter")

        Domain.__init__(self, desc)
        self.min = Duration(self.min)
        self.max = Duration(self.max)
        self.interval = Duration(self.interval)

        self.key = "min"
        self.partitions = list_to_data([
            {"min": v, "max": v + self.interval, "dataIndex": i}
            for i, v in enumerate(Duration.range(self.min, self.max, self.interval))
        ])

    def compare(self, a, b):
        return value_compare(a, b)

    def getCanonicalPart(self, part):
        return self.getPartByKey(part[self.key])

    def getIndexByKey(self, key):
        for p in self.partitions:
            if p.min <= key < p.max:
                return p.dataIndex
        return len(self.partitions)

    def getPartByKey(self, key):
        for p in self.partitions:
            if p.min <= key < p.max:
                return p
        return Null

    def getKey(self, part):
        return part[self.key]

    def getKeyByIndex(self, index):
        return self.partitions[index][self.key]

    def __data__(self):
        output = Domain.__data__(self)

        output.partitions = self.partitions
        output.min = self.min
        output.max = self.max
        output.interval = self.interval
        return output


class NumericDomain(Domain):
    # ZERO DIMENSIONAL RANGE

    __slots__ = ["max", "min"]

    @override(kwargs="desc")
    def __new__(cls, partitions=None, interval=None, desc=None):
        if not partitions and not interval:
            return object.__new__(cls)
        else:
            return object.__new__(RangeDomain)

    @override(kwargs="desc")
    def __init__(
        self,
        type="range",
        name=None,
        value=None,
        key=None,
        label=None,
        end=None,
        is_facet=False,
        where=None,
        primitive=None,
        limit=None,
        min=None,
        max=None,
        desc=None,
    ):
        Domain.__init__(self, desc)

    def compare(self, a, b):
        return value_compare(a, b)

    def getCanonicalPart(self, part):
        return part

    def getIndexByKey(self, key):
        return key

    def getPartByKey(self, key):
        if self.min != None and key < self.min:
            return Null
        if self.max != None and key >= self.max:
            return Null
        return key

    def getKey(self, part):
        return part

    def getKeyByIndex(self, index):
        return index

    def __data__(self):
        output = Domain.__data__(self)

        output.min = self.min
        output.max = self.max
        return output


class UniqueDomain(Domain):
    __slots__ = ()

    def compare(self, a, b):
        return value_compare(a, b)

    def getCanonicalPart(self, part):
        return part

    def getPartByKey(self, key):
        return key

    def getKey(self, part):
        return part

    def getEnd(self, value):
        return value


class RangeDomain(Domain):
    __slots__ = ["max", "min", "interval", "partitions"]

    @override(kwargs="desc")
    def __init__(
        self,
        type="range",
        name=None,
        value=None,
        key=None,
        label=None,
        end=None,
        is_facet=False,
        where=None,
        primitive=None,
        limit=None,
        min=None,
        max=None,
        interval=None,  # FOR EQUAL_SPACED PARTITIONS
        partitions=None,
        desc=None,
    ):
        Domain.__init__(self, desc)
        self.type = "range"
        self.element_type = JxType(min=JX_NUMBER, max=JX_NUMBER, dataIndex=JX_INTEGER)

        if partitions:
            # IGNORE THE min, max, interval
            if not key:
                Log.error("Must have a key value")

            parts = enlist(partitions)
            for i, p in enumerate(parts):
                self.min = MIN([min, p.min])
                self.max = MAX([max, p.max])
                if p.dataIndex != None and p.dataIndex != i:
                    Log.error("Expecting `dataIndex` to agree with the order of the parts")
                if p[key] == None:
                    Log.error(
                        "Expecting all parts to have {{key}} as a property", key=key,
                    )
                p.dataIndex = i

            # VERIFY PARTITIONS DO NOT OVERLAP, HOLES ARE FINE
            for p, q in itertools.product(parts, parts):
                if p.min <= q.min < p.max and from_data(p) is not from_data(q):
                    Log.error("partitions overlap!")

            self.partitions = parts
            return
        elif any([min == None, max == None, interval == None]):
            Log.error("Can not handle missing parameter")

        self.key = "min"
        self.partitions = list_to_data([
            {"min": v, "max": v + interval, "dataIndex": i} for i, v in enumerate(frange(min, max, interval))
        ])

    def compare(self, a, b):
        return value_compare(a, b)

    def getCanonicalPart(self, part):
        return self.getPartByKey(part[self.key])

    def getIndexByKey(self, key):
        for p in self.partitions:
            if p.min <= key < p.max:
                return p.dataIndex
        return len(self.partitions)

    def getPartByKey(self, key):
        for p in self.partitions:
            if p.min <= key < p.max:
                return p
        return Null

    def getKey(self, part):
        return part[self.key]

    def getKeyByIndex(self, index):
        return self.partitions[index][self.key]

    def __data__(self):
        output = Domain.__data__(self)

        output.partitions = self.partitions
        output.min = self.min
        output.max = self.max
        output.interval = self.interval
        return output


def frange(start, stop, step):
    # LIKE range(), BUT FOR FLOATS
    output = start
    while output < stop:
        yield output
        output += step


def value_compare(a, b):
    if a == None:
        if b == None:
            return 0
        return -1
    elif b == None:
        return 1

    if a > b:
        return 1
    elif a < b:
        return -1
    else:
        return 0


name_to_type = {
    "value": ValueDomain,
    "default": DefaultDomain,
    "set": SimpleSetDomain,
    "time": TimeDomain,
    "duration": DurationDomain,
    "range": RangeDomain,
    "uid": UniqueDomain,
    "numeric": NumericDomain,
}
