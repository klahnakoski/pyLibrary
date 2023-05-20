# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#

from jx_base import DataClass

from mo_dots import is_list, join_field
from mo_json import *
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
    elif isinstance(v, str):
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
    if len(sql_key) != 2 or sql_key[0] != SQL_KEY_PREFIX:
        Log.error("not expected")
    return concat_field(name, sql_key)


def untyped_column(column_name):
    """
    :param column_name:  DATABASE COLUMN NAME
    :return: (NAME, TYPE) PAIR
    """
    if "$" in column_name:
        path = split_field(column_name)
        if path[-1] in SQL_KEYS:
            return join_field([p for p in path[:-1] if p != SQL_ARRAY_KEY]), path[-1][1:]
        else:
            return join_field([p for p in path if p != SQL_ARRAY_KEY]), None
    elif column_name in [GUID]:
        return column_name, SQL_NUMBER_KEY
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


SQL_KEY_PREFIX = "$"

SQL_IS_NULL_KEY = SQL_KEY_PREFIX + "0"
SQL_BOOLEAN_KEY = SQL_KEY_PREFIX + "B"
SQL_NUMBER_KEY = SQL_KEY_PREFIX + "N"
SQL_TIME_KEY = SQL_KEY_PREFIX + "T"
SQL_INTERVAL_KEY = SQL_KEY_PREFIX + "N"
SQL_STRING_KEY = SQL_KEY_PREFIX + "S"
SQL_OBJECT_KEY = SQL_KEY_PREFIX + "J"
SQL_ARRAY_KEY = SQL_KEY_PREFIX + "A"


SQL_KEYS = [
    SQL_IS_NULL_KEY,
    SQL_BOOLEAN_KEY,
    SQL_NUMBER_KEY,
    SQL_TIME_KEY,
    SQL_INTERVAL_KEY,
    SQL_STRING_KEY,
    SQL_OBJECT_KEY,
    SQL_ARRAY_KEY
]

json_type_to_sql_type_key = {
    IS_NULL: SQL_IS_NULL_KEY,
    BOOLEAN: SQL_BOOLEAN_KEY,
    NUMBER: SQL_NUMBER_KEY,
    TIME: SQL_TIME_KEY,
    INTERVAL: SQL_INTERVAL_KEY,
    STRING: SQL_STRING_KEY,
    OBJECT: SQL_OBJECT_KEY,
    ARRAY: SQL_ARRAY_KEY,
}

sql_type_key_to_json_type = {
    None: None,
    SQL_IS_NULL_KEY: IS_NULL,
    SQL_BOOLEAN_KEY: BOOLEAN,
    SQL_NUMBER_KEY: NUMBER,
    SQL_STRING_KEY: STRING,
    SQL_OBJECT_KEY: OBJECT,
    SQL_ARRAY_KEY: ARRAY,
}

jx_type_to_sql_type_key = {
    JX_IS_NULL: SQL_IS_NULL_KEY,
    JX_BOOLEAN: SQL_BOOLEAN_KEY,
    JX_NUMBER: SQL_NUMBER_KEY,
    JX_TIME: SQL_TIME_KEY,
    JX_INTERVAL: SQL_INTERVAL_KEY,
    JX_TEXT: SQL_STRING_KEY,
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
