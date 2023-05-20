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
    NotRightOp as NotRightOp_,
    LengthOp,
    MaxOp,
    SubOp,
    Literal,
    ZERO,
)
from jx_sqlite.expressions._utils import check, OrOp, SQLang
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import SQL_ONE
from jx_sqlite.sqlite import sql_call
from mo_json import JX_TEXT


class NotRightOp(NotRightOp_):
    @check
    def to_sql(self, schema):
        v = self.value.to_sql(schema)
        if self.length == ZERO:
            return v

        r = self.length.to_sql(schema)
        end = (
            MaxOp([ZERO, SubOp([LengthOp(self.value), MaxOp([ZERO, self.length])])])
            .partial_eval(SQLang)
            .to_sql(schema)
        )
        sql = sql_call("SUBSTR", v.frum, SQL_ONE, end)
        return SqlScript(
            data_type=JX_TEXT,
            expr=sql,
            frum=self,
            miss=OrOp([r.miss, v.miss]),
            schema=schema,
        )
