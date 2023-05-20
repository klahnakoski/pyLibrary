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

from jx_base.expressions import SqlEqOp as SqlEqOp_, is_literal, AndOp, FALSE
from jx_sqlite.expressions._utils import SQLang, check, SqlScript
from jx_sqlite.expressions.to_boolean_op import ToBooleanOp
from jx_sqlite.sqlite import SQL_OR, ConcatSQL, SQL_EQ
from mo_json import JX_BOOLEAN
from mo_logs import Log


class SqlEqOp(SqlEqOp_):
    @check
    def to_sql(self, schema):
        lhs = self.lhs.partial_eval(SQLang)
        rhs = self.rhs.partial_eval(SQLang)
        if is_literal(lhs) and lhs.value in ("T", "F"):
            lhs = ToBooleanOp(lhs).to_sql(schema)
        if is_literal(rhs) and rhs.value in ("T", "F"):
            rhs = ToBooleanOp(rhs).to_sql(schema)

        lhs_sql = lhs.to_sql(schema)
        rhs_sql = rhs.to_sql(schema)

        lleaves = list(lhs_sql.type.leaves())
        rleaves = list(rhs_sql.type.leaves())
        if len(lleaves) == 1 and len(rleaves) == 1 and lleaves[0][1] == rleaves[0][1]:
            pass
        else:
            Log.error("Not supported yet")

        null_match = AndOp([
            lhs.missing(SQLang),
            rhs.missing(SQLang),
        ]).partial_eval(SQLang)
        if null_match is FALSE:
            sql = ConcatSQL(lhs_sql, SQL_EQ, rhs_sql)
        else:
            sql = ConcatSQL(lhs_sql, SQL_EQ, rhs_sql, SQL_OR, null_match.to_sql(schema))

        return SqlScript(
            data_type=JX_BOOLEAN, expr=sql, frum=self, miss=FALSE, schema=schema
        )
