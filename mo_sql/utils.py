# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#

from math import isnan

from jx_base import DataClass

from mo_dots import (
    concat_field,
    is_data,
    is_list,
    join_field,
    split_field,
    is_sequence,
)
from mo_future import is_text, POS_INF
from mo_json import (
    BOOLEAN,
    ARRAY,
    NUMBER,
    OBJECT,
    STRING,
    T_BOOLEAN,
    T_TEXT,
    T_NUMBER,
    IS_NULL,
    TIME,
    INTERVAL,
    T_IS_NULL,
    T_TIME,
    T_INTERVAL,
)
from mo_logs import Log
from mo_math import randoms
from mo_times import Date

DIGITS_TABLE = "__digits__"
ABOUT_TABLE = "meta.about"


GUID = "_id"  # user accessible, unique value across many machines
UID = "__id__"  # internal numeric id for single-database use
ORDER = "__order__"
PARENT = "__parent__"
COLUMN = "__column"

ALL_TYPES = "bns"


def unique_name():
    return randoms.string(20)


def column_key(k, v):
    if v == None:
        return None
    elif isinstance(v, bool):
        return k, "boolean"
    elif is_text(v):
        return k, "string"
    elif is_list(v):
        return k, None
    elif is_data(v):
        return k, "object"
    elif isinstance(v, Date):
        return k, "number"
    else:
        return k, "number"


def typed_column(name, sql_key):
    if len(sql_key) > 1:
        Log.error("not expected")
    return concat_field(name, "$" + sql_key)


def untyped_column(column_name):
    """
    :param column_name:  DATABASE COLUMN NAME
    :return: (NAME, TYPE) PAIR
    """
    if "$" in column_name:
        path = split_field(column_name)
        return join_field([p for p in path[:-1] if p != "$a"]), path[-1][1:]
    elif column_name in [GUID]:
        return column_name, "n"
    else:
        return column_name, None


untype_field = untyped_column

sql_aggs = {
    "avg": "AVG",
    "average": "AVG",
    "count": "COUNT",
    "first": "FIRST_VALUE",
    "last": "LAST_VALUE",
    "max": "MAX",
    "maximum": "MAX",
    "median": "MEDIAN",
    "min": "MIN",
    "minimum": "MIN",
    "sum": "SUM",
    "add": "SUM",
}

STATS = {
    "count": "COUNT({{value}})",
    "std": "SQRT((1-1.0/COUNT({{value}}))*VARIANCE({{value}}))",
    "min": "MIN({{value}})",
    "max": "MAX({{value}})",
    "sum": "SUM({{value}})",
    "median": "MEDIAN({{value}})",
    "sos": "SUM({{value}}*{{value}})",
    "var": "(1-1.0/COUNT({{value}}))*VARIANCE({{value}})",
    "avg": "AVG({{value}})",
}


SQL_IS_NULL_KEY = "0"
SQL_BOOLEAN_KEY = "B"
SQL_NUMBER_KEY = "N"
SQL_TIME_KEY = "T"
SQL_INTERVAL_KEY = "N"
SQL_STRING_KEY = "S"
SQL_OBJECT_KEY = "J"
SQL_ARRAY_KEY = "A"

json_type_to_sql_type_key = {
    IS_NULL: SQL_IS_NULL_KEY,
    BOOLEAN: SQL_BOOLEAN_KEY,
    NUMBER: SQL_NUMBER_KEY,
    TIME: SQL_TIME_KEY,
    INTERVAL: SQL_INTERVAL_KEY,
    STRING: SQL_STRING_KEY,
    OBJECT: SQL_OBJECT_KEY,
    ARRAY: SQL_ARRAY_KEY,
    T_IS_NULL: SQL_IS_NULL_KEY,
    T_BOOLEAN: SQL_BOOLEAN_KEY,
    T_NUMBER: SQL_NUMBER_KEY,
    T_TIME: SQL_TIME_KEY,
    T_INTERVAL: SQL_INTERVAL_KEY,
    T_TEXT: SQL_STRING_KEY,
}

sql_type_key_to_json_type = {
    None: None,
    "0": IS_NULL,
    "b": BOOLEAN,
    "n": NUMBER,
    "s": STRING,
    "j": OBJECT,
}


ColumnMapping = DataClass(
    "ColumnMapping",
    [
        {  # EDGES ARE AUTOMATICALLY INCLUDED IN THE OUTPUT, USE THIS TO INDICATE EDGES SO WE DO NOT DOUBLE-PRINT
            "name": "is_edge",
            "default": False,
        },
        {  # TRACK NUMBER OF TABLE COLUMNS THIS column REPRESENTS
            "name": "num_push_columns",
            "nulls": True,
        },
        {  # NAME OF THE PROPERTY (USED BY LIST FORMAT ONLY)
            "name": "push_list_name",
            "nulls": True,
        },
        {  # PATH INTO COLUMN WHERE VALUE IS STORED ("." MEANS COLUMN HOLDS PRIMITIVE VALUE)
            "name": "push_column_child",
            "nulls": True,
        },
        {"name": "push_column_index", "nulls": True},  # THE COLUMN NUMBER
        {  # THE COLUMN NAME FOR TABLES AND CUBES (WITH NO ESCAPING DOTS, NOT IN LEAF FORM)
            "name": "push_column_name",
            "nulls": True,
        },
        {"name": "pull", "nulls": True},  # A FUNCTION THAT WILL RETURN A VALUE
        {  # A LIST OF MULTI-SQL REQUIRED TO GET THE VALUE FROM THE DATABASE
            "name": "sql",
        },
        "type",  # THE NAME OF THE JSON DATA TYPE EXPECTED
        {  # A LIST OF PATHS EACH INDICATING AN ARRAY
            "name": "nested_path",
            "type": list,
            "default": ["."],
        },
        "column_alias",
    ],
    constraint={"and": [
        {"in": {"type": ["0", "boolean", "number", "string", "object"]}},
        {"gte": [{"length": "nested_path"}, 1]},
    ]},
)
