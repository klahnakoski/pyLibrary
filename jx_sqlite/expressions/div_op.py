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
    DivOp as DivOp_,
    TRUE,
    MissingOp,
    AndOp,
    OrOp,
    ToNumberOp,
)
from jx_sqlite.expressions._utils import SQLang, check, SqlScript
from jx_sqlite.sqlite import sql_iso, ConcatSQL, sql_call, SQL_DIV
from mo_json import JX_NUMBER


class DivOp(DivOp_):
    @check
    def to_sql(self, schema):
        lhs = ToNumberOp(self.lhs).partial_eval(SQLang).to_sql(schema)
        rhs = ToNumberOp(self.rhs).partial_eval(SQLang).to_sql(schema)
        d = self.default.partial_eval(SQLang).to_sql(schema)

        if d.miss is TRUE:
            return SqlScript(
                data_type=JX_NUMBER,
                expr=ConcatSQL(sql_iso(lhs), SQL_DIV, sql_iso(rhs)),
                frum=self,
                miss=OrOp([MissingOp(self.lhs), MissingOp(self.rhs)]),
                schema=schema,
            )
        else:
            return SqlScript(
                data_type=JX_NUMBER | d.type,
                expr=sql_call(
                    "COALESCE", ConcatSQL(sql_iso(lhs), SQL_DIV, sql_iso(rhs)), d
                ),
                frum=self,
                miss=AndOp([
                    self.default.missing(SQLang),
                    OrOp([MissingOp(self.lhs), MissingOp(self.rhs)]),
                ]),
                schema=schema,
            )
