# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import datetime

from mo_collections import UniqueIndex
from mo_dots import (
    Data,
    FlatList,
    NullType,
    concat_field,
    is_container,
    join_field,
    split_field,
    to_data,
)
from mo_future import Mapping
from mo_future import binary_type, items, long, none_type, reduce, text
from mo_imports import export
from mo_logs import strings
from mo_times.dates import Date

from jx_base import DataClass
from jx_base.models.schema import Schema
from jx_base.utils import enlist, delist
from mo_json import (
    INTEGER,
    NUMBER,
    STRING,
    python_type_to_jx_type,
    OBJECT,
    true,
    EXISTS,
    ARRAY,
)
from mo_json.typed_encoder import json_type_to_inserter_type, EXISTS_KEY

DEBUG = False
META_TABLES_NAME = "meta.tables"
META_COLUMNS_NAME = "meta.columns"
META_COLUMNS_TYPE_NAME = "column"
ROOT_PATH = [META_COLUMNS_NAME]
singlton = None

strings

TableDesc = DataClass(
    "Table",
    ["name", {"name": "url", "nulls": true}, "query_path", {"name": "last_updated", "nulls": False}, "columns"],
    constraint={"and": [{"ne": [{"last": "query_path"}, {"literal": "."}]}]},
)

Column = DataClass(
    "Column",
    [
        "name",
        "es_column",
        "es_index",
        "es_type",
        "json_type",
        "nested_path",  # AN ARRAY OF PATHS (FROM DEEPEST TO SHALLOWEST) INDICATING THE JSON SUB-ARRAYS
        {"name": "count", "nulls": True},
        {"name": "cardinality", "nulls": True},
        {"name": "multi", "nulls": False},
        {"name": "partitions", "nulls": True},
        "last_updated",
    ],
    constraint={"and": [
        {
            "when": {"ne": {"name": "."}},
            "then": {"or": [
                {"and": [{"eq": {"json_type": "object"}}, {"eq": {"multi": 1}}]},
                {"ne": ["name", {"first": "nested_path"}]},
            ]},
            "else": True,
        },
        {"when": {"eq": {"es_column": "."}}, "then": {"in": {"json_type": ["nested", "object"]}}, "else": True},
        {"not": {"find": {"es_column": "null"}}},
        {"not": {"eq": {"es_column": "string"}}},
        {"not": {"eq": {"es_type": "object", "json_type": "exists"}}},
        {"when": {"suffix": {"es_column": "." + EXISTS_KEY}}, "then": {"eq": {"json_type": EXISTS}}, "else": True},
        {"when": {"suffix": {"es_column": "." + EXISTS_KEY}}, "then": {"exists": "cardinality"}, "else": True},
        {"when": {"eq": {"json_type": OBJECT}}, "then": {"in": {"cardinality": [0, 1]}}, "else": True},
        {"when": {"eq": {"json_type": ARRAY}}, "then": {"in": {"cardinality": [0, 1]}}, "else": True},
        {"not": {"prefix": [{"first": "nested_path"}, {"literal": "testdata"}]}},
        {"ne": [{"last": "nested_path"}, {"literal": "."}]},  # NESTED PATHS MUST BE REAL TABLE NAMES INSIDE Namespace
        {
            "when": {"eq": [{"literal": ".~N~"}, {"right": {"es_column": 4}}]},
            "then": {"or": [
                {"and": [{"gt": {"multi": 1}}, {"eq": {"json_type": "nested"}}, {"eq": {"es_type": "nested"}}]},
                {"and": [{"eq": {"multi": 1}}, {"eq": {"json_type": "object"}}, {"eq": {"es_type": "object"}}]},
            ]},
            "else": True,
        },
        {
            "when": {"gte": [{"count": "nested_path"}, 2]},
            "then": {"ne": [{"first": {"right": {"nested_path": 2}}}, {"literal": "."}]},  # SECOND-LAST ELEMENT
            "else": True,
        },
    ]},
)


def get_schema_from_list(table_name, frum, native_type_to_json_type=python_type_to_jx_type):
    """
    SCAN THE LIST FOR COLUMN TYPES
    """
    columns = UniqueIndex(keys=("name",))
    _get_schema_from_list(
        frum,
        ".",
        parent=".",
        nested_path=ROOT_PATH,
        columns=columns,
        native_type_to_json_type=native_type_to_json_type,
    )
    return Schema(table_name=table_name, columns=list(columns))


def _get_schema_from_list(
    frum,  # The list
    table_name,  # Name of the table this list holds records for
    parent,  # parent path
    nested_path,  # each nested array, in reverse order
    columns,  # map from full name to column definition
    native_type_to_json_type,  # dict from storage type name to json type name
):
    for d in frum:
        row_type = python_type_to_jx_type[d.__class__]

        if row_type != "object":
            # EXPECTING PRIMITIVE VALUE
            full_name = parent
            column = columns[full_name]
            if not column:
                es_type = d.__class__
                json_type = native_type_to_json_type[es_type]

                column = Column(
                    name=concat_field(table_name, json_type_to_inserter_type[json_type]),
                    es_column=full_name,
                    es_index=".",
                    es_type=es_type,
                    json_type=json_type,
                    last_updated=Date.now(),
                    nested_path=nested_path,
                    multi=1,
                )
                columns.add(column)
            else:
                column.es_type = _merge_python_type(column.es_type, d.__class__)
                column.json_type = native_type_to_json_type[column.es_type]
        else:
            for name, value in d.items():
                full_name = concat_field(parent, name)
                column = columns[full_name]

                if is_container(value):  # GET TYPE OF MULTIVALUE
                    v = list(value)
                    if len(v) == 0:
                        es_type = none_type.__name__
                    elif len(v) == 1:
                        es_type = v[0].__class__.__name__
                    else:
                        es_type = reduce(_merge_python_type, (vi.__class__.__name__ for vi in value))
                else:
                    es_type = value.__class__.__name__

                if not column:
                    json_type = native_type_to_json_type[es_type]
                    column = Column(
                        name=concat_field(table_name, full_name),
                        es_column=full_name,
                        es_index=".",
                        es_type=es_type,
                        json_type=json_type,
                        last_updated=Date.now(),
                        nested_path=nested_path,
                        cardinality=1 if json_type == OBJECT else None,
                        multi=1,
                    )
                    columns.add(column)
                else:
                    column.es_type = _merge_python_type(column.es_type, es_type)
                    try:
                        column.json_type = native_type_to_json_type[column.es_type]
                    except Exception as e:
                        raise e

                if es_type in {"object", "dict", "Mapping", "Data"}:
                    _get_schema_from_list(
                        [value], table_name, full_name, nested_path, columns, native_type_to_json_type,
                    )
                elif es_type in {"list", "FlatList"}:
                    np = enlist(nested_path)
                    newpath = delist([join_field(split_field(np[0]) + [name])] + np)
                    _get_schema_from_list(value, table_name, full_name, newpath, columns)


def get_id(column):
    """
    :param column:
    :return: Elasticsearch id for column
    """
    return column.es_index + "|" + column.es_column


try:
    META_COLUMNS_DESC = TableDesc(
        name=META_COLUMNS_NAME,
        url=None,
        query_path=ROOT_PATH,
        last_updated=Date.now(),
        columns=to_data(
            [
                Column(
                    name=c,
                    es_index=META_COLUMNS_NAME,
                    es_column=c,
                    es_type="keyword",
                    json_type=STRING,
                    last_updated=Date.now(),
                    nested_path=ROOT_PATH,
                    multi=1,
                )
                for c in ["name", "es_type", "json_type", "es_column", "es_index", "partitions"]
            ]
            + [
                Column(
                    name=c,
                    es_index=META_COLUMNS_NAME,
                    es_column=c,
                    es_type="integer",
                    json_type=INTEGER,
                    last_updated=Date.now(),
                    nested_path=ROOT_PATH,
                    multi=1,
                )
                for c in ["count", "cardinality", "multi"]
            ]
            + [
                Column(
                    name="nested_path",
                    es_index=META_COLUMNS_NAME,
                    es_column="nested_path",
                    es_type="keyword",
                    json_type=STRING,
                    last_updated=Date.now(),
                    nested_path=ROOT_PATH,
                    multi=4,
                ),
                Column(
                    name="last_updated",
                    es_index=META_COLUMNS_NAME,
                    es_column="last_updated",
                    es_type="double",
                    json_type=NUMBER,
                    last_updated=Date.now(),
                    nested_path=ROOT_PATH,
                    multi=1,
                ),
            ]
        ),
    )
except Exception as cause:
    print(cause)

META_TABLES_DESC = TableDesc(
    name=META_TABLES_NAME,
    url=None,
    query_path=ROOT_PATH,
    last_updated=Date.now(),
    columns=to_data(
        [
            Column(
                name=c,
                es_index=META_TABLES_NAME,
                es_column=c,
                es_type="string",
                json_type=STRING,
                last_updated=Date.now(),
                nested_path=ROOT_PATH,
                multi=1,
            )
            for c in ["name", "url", "query_path"]
        ]
        + [
            Column(
                name=c,
                es_index=META_TABLES_NAME,
                es_column=c,
                es_type="integer",
                json_type=INTEGER,
                last_updated=Date.now(),
                nested_path=ROOT_PATH,
                multi=1,
            )
            for c in ["timestamp"]
        ]
    ),
)


SIMPLE_METADATA_COLUMNS = (  # FOR PURELY INTERNAL PYTHON LISTS, NOT MAPPING TO ANOTHER DATASTORE
    [
        Column(
            name=c,
            es_index=META_COLUMNS_NAME,
            es_column=c,
            es_type="string",
            json_type=STRING,
            last_updated=Date.now(),
            nested_path=ROOT_PATH,
            multi=1,
        )
        for c in ["table", "name", "type"]
    ]
    + [
        Column(
            name=c,
            es_index=META_COLUMNS_NAME,
            es_column=c,
            es_type="long",
            json_type=INTEGER,
            last_updated=Date.now(),
            nested_path=ROOT_PATH,
            multi=1,
        )
        for c in ["count", "cardinality", "multi"]
    ]
    + [
        Column(
            name="last_updated",
            es_index=META_COLUMNS_NAME,
            es_column="last_updated",
            es_type="time",
            json_type=NUMBER,
            last_updated=Date.now(),
            nested_path=ROOT_PATH,
            multi=1,
        ),
        Column(
            name="nested_path",
            es_index=META_COLUMNS_NAME,
            es_column="nested_path",
            es_type="string",
            json_type=STRING,
            last_updated=Date.now(),
            nested_path=ROOT_PATH,
            multi=4,
        ),
    ]
)

_merge_order = {
    none_type: 0,
    NullType: 1,
    bool: 2,
    int: 3,
    long: 3,
    Date: 4,
    datetime: 4,
    float: 5,
    text: 6,
    binary_type: 6,
    object: 7,
    dict: 8,
    Mapping: 9,
    Data: 10,
    list: 11,
    FlatList: 12,
}

for k, v in items(_merge_order):
    _merge_order[k.__name__] = v


def _merge_python_type(A, B):
    a = _merge_order[A]
    b = _merge_order[B]

    if a >= b:
        output = A
    else:
        output = B

    if isinstance(output, str):
        return output
    else:
        return output.__name__


export("jx_base.expressions.query_op", Column)
