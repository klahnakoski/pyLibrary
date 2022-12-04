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
    SubOp as SubOp_,
    TRUE,
    OrOp,
    MissingOp,
    AndOp,
    IsNumberOp,
    NULL,
)
from jx_sqlite.expressions._utils import _binaryop_to_sql, check, SQLang
from jx_sqlite.expressions.sql_script import SqlScript
from mo_json import T_NUMBER
from jx_sqlite.sqlite import ConcatSQL, sql_iso, SQL_SUB, sql_call


class SubOp(SubOp_):
    to_sql = _binaryop_to_sql

    @check
    def to_sql(self, schema):
        lhs = IsNumberOp(self.lhs).partial_eval(SQLang).to_sql(schema)
        rhs = self.rhs.partial_eval(SQLang).to_sql(schema)
        d = self.default.partial_eval(SQLang).to_sql(schema)

        if lhs.miss is TRUE or rhs.miss is TRUE:
            if d.miss is TRUE:
                return NULL.to_sql(schema)
            else:
                return d

        sql = ConcatSQL(sql_iso(lhs.frum), SQL_SUB, sql_iso(rhs.frum))

        if d.miss is not TRUE:
            sql = sql_call("COALESCE", sql, d.frum)

        return SqlScript(
            data_type=T_NUMBER,
            expr=sql,
            frum=self,
            miss=AndOp([
                OrOp([MissingOp(self.lhs), MissingOp(self.rhs)]),
                MissingOp(self.default)
            ]), schema=schema
        )
