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
    BasicEqOp as BasicEqOp_,
    FALSE,
    is_literal,
    NotOp,
    ToBooleanOp,
)
from jx_sqlite.expressions._utils import check, SQLang
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import sql_iso, SQL_EQ
from mo_json.types import JX_BOOLEAN
from mo_sql import ConcatSQL, SQL_NOT
from pyLibrary.convert import value2boolean


class BasicEqOp(BasicEqOp_):
    def partial_eval(self, lang):
        lhs = self.lhs.partial_eval(lang)
        rhs = self.rhs.partial_eval(lang)
        if is_literal(rhs) and rhs.value == 0:
            lhs._data_type = JX_BOOLEAN
            return NotOp(lhs)
        if is_literal(lhs) and lhs.value == 0:
            rhs._data_type = JX_BOOLEAN
            return NotOp(rhs)
        return BasicEqOp([lhs, rhs])

    @check
    def to_sql(self, schema):
        rhs = self.rhs.partial_eval(SQLang)
        lhs = self.lhs.partial_eval(SQLang)

        if is_literal(lhs):
            lhs, rhs = rhs, lhs
        if is_literal(rhs):
            lhs = lhs.to_sql(schema)
            if lhs._data_type == JX_BOOLEAN:
                if value2boolean(rhs.value):
                    return lhs
                else:
                    return NotOp(lhs.frum).partial_eval(SQLang).to_sql(schema)
        return SqlScript(
            data_type=JX_BOOLEAN,
            expr=ConcatSQL(
                sql_iso(lhs.to_sql(schema)), SQL_EQ, sql_iso(rhs.to_sql(schema)),
            ),
            frum=self,
            miss=FALSE, schema=schema
        )
