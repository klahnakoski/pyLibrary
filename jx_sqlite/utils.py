# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from __future__ import absolute_import, division, unicode_literals

from copy import copy

from jx_sqlite.sqlite import quote_column, SQL_DESC, SQL_ASC
from mo_dots import Data, is_missing
from mo_future import text
from mo_json import json2value, INTEGER
from mo_json.typed_encoder import untype_path
from mo_json.types import _B, _I, _N, _S, _A, T_ARRAY, T_INTEGER
from mo_sql.utils import *
from mo_times import Date



def table_alias(i):
    """
    :param i:
    :return:
    """
    return "__t" + text(i) + "__"


def get_document_value(document, column):
    """
    RETURN DOCUMENT VALUE IF MATCHES THE column (name, type)

    :param document: THE DOCUMENT
    :param column: A (name, type) PAIR
    :return: VALUE, IF IT IS THE SAME NAME AND TYPE
    """
    v = document.get(split_field(column.name)[0], None)
    return get_if_type(v, column.type)


def get_if_type(value, type):
    if is_type(value, type):
        if type == "object":
            return "."
        if isinstance(value, Date):
            return value.unix
        return value
    return None


def is_type(value, type):
    if value == None:
        return False
    elif is_text(value) and type == "string":
        return value
    elif is_list(value):
        return False
    elif is_data(value) and type == "object":
        return True
    elif isinstance(value, (int, float, Date)) and type == "number":
        return True
    return False


def _make_column_name(number):
    return COLUMN + text(number)

quoted_GUID = quote_column(GUID)
quoted_UID = quote_column(UID)
quoted_ORDER = quote_column(ORDER)
quoted_PARENT = quote_column(PARENT)


def sql_text_array_to_set(column):
    def _convert(row):
        text = row[column]
        if text == None:
            return set()
        else:
            value = json2value(row[column])
            return set(value) - {None}

    return _convert


def get_column(column, json_type=None, default=None):
    """
    :param column: The column you want extracted
    :return: a function that can pull the given column out of sql resultset
    """

    to_type = json_type_to_python_type.get(json_type)

    if to_type is None:
        def _get(row):
            value = row[column]
            if is_missing(value):
                return default
            return value

        return _get

    def _get_type(row):
        value = row[column]
        if is_missing(value):
            return default
        return to_type(value)

    return _get_type


json_type_to_python_type = {T_BOOLEAN: bool}


def set_column(row, col, child, value):
    """
    EXECUTE `row[col][child]=value` KNOWING THAT row[col] MIGHT BE None
    :param row:
    :param col:
    :param child:
    :param value:
    :return:
    """
    if child == ".":
        row[col] = value
    else:
        column = row[col]

        if column is None:
            column = row[col] = {}
        Data(column)[child] = value


def copy_cols(cols, nest_to_alias):
    """
    MAKE ALIAS FOR EACH COLUMN
    :param cols:
    :param nest_to_alias:  map from nesting level to subquery alias
    :return:
    """
    output = set()
    for c in cols:
        c = copy(c)
        c.es_index = nest_to_alias[c.nested_path[0]]
        output.add(c)
    return output


sqlite_type_to_simple_type = {
    "TEXT": STRING,
    "REAL": NUMBER,
    "INT": INTEGER,
    "INTEGER": INTEGER,
    "TINYINT": BOOLEAN,
}

sqlite_type_to_type_key = {
    "ARRAY": _A,
    "TEXT": _S,
    "REAL": _N,
    "INTEGER": _I,
    "TINYINT": _B,
    "TRUE": _B,
    "FALSE": _B,
}

type_key_json_type = {
    _A: T_ARRAY,
    _S: T_TEXT,
    _N: T_NUMBER,
    _I: T_INTEGER,
    _B: T_BOOLEAN,
}

sort_to_sqlite_order = {
    -1: SQL_DESC,
    0: SQL_ASC,
    1: SQL_ASC
}


class ColumnLocator(object):
    def __init__(self, columns):
        self.columns = columns

    def __getitem__(self, column_name):
        return [c for c in self.columns if untype_path(c.name) == column_name]
