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

from jx_base.expressions import (
    FALSE,
    SqlScript as SQLScript_,
    TRUE,
    Variable,
)
from jx_base.language import is_op
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.sqlite import (
    SQL,
    SQL_CASE,
    SQL_END,
    SQL_NULL,
    SQL_THEN,
    SQL_WHEN,
    sql_iso,
    ConcatSQL,
    SQL_NOT,
)
from mo_future import PY2, text
from mo_imports import export
from mo_json import JxType
from mo_logs import Log


class SqlScript(SQLScript_, SQL):
    __slots__ = ("_data_type", "expr", "frum", "miss", "schema")

    def __init__(self, data_type, expr, frum, miss=None, schema=None):
        object.__init__(self)
        if expr == None:
            Log.error("expecting expr")
        if not isinstance(expr, SQL):
            Log.error("Expecting SQL")
        if not isinstance(data_type, JxType):
            Log.error("Expecting JxType")
        if schema is None:
            Log.error("expecting schema")

        if miss is None:
            self.miss = frum.missing(SQLang)
        else:
            self.miss = miss
        self._data_type = data_type  # JSON DATA TYPE
        self.expr = expr
        self.frum = frum  # THE ORIGINAL EXPRESSION THAT MADE expr
        self.schema = schema

    @property
    def type(self):
        return self._data_type

    @property
    def name(self):
        return "."

    def __getitem__(self, item):
        if not self.many:
            if item == 0:
                return self
            else:
                Log.error("this is a primitive value")
        else:
            Log.error("do not know how to handle")

    def __iter__(self):
        """
        ASSUMED TO OVERRIDE SQL.__iter__()
        """
        return self.sql.__iter__()

    def to_sql(self, schema):
        return self

    @property
    def sql(self):
        self.miss = self.miss.partial_eval(SQLang)
        if self.miss is TRUE:
            return SQL_NULL
        elif self.miss is FALSE or is_op(self.frum, Variable):
            return self.expr

        missing = self.miss.partial_eval(SQLang).to_sql(self.schema)
        return ConcatSQL(
            SQL_CASE, SQL_WHEN, SQL_NOT, sql_iso(missing), SQL_THEN, self.expr, SQL_END,
        )

    def __str__(self):
        return str(self.sql)

    def __unicode__(self):
        return text(self.sql)

    def __add__(self, other):
        return text(self) + text(other)

    def __radd__(self, other):
        return text(other) + text(self)

    if PY2:
        __unicode__ = __str__

    @check
    def to_sql(self, schema):
        return self

    def missing(self, lang):
        return self.miss

    def __data__(self):
        return {"script": self.script}

    def __eq__(self, other):
        if not isinstance(other, SQLScript_):
            return False
        elif self.expr == other.frum:
            return True
        else:
            return False


export("jx_sqlite.expressions._utils", SqlScript)
export("jx_sqlite.expressions.or_op", SqlScript)
