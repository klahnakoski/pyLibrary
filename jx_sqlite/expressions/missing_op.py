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

from jx_base.expressions import MissingOp as MissingOp_, FALSE
from jx_base.language import is_op
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import ConcatSQL, SQL_IS_NULL, SQL_NOT, sql_call, SQL_OR, sql_iso, SQL_EQ, TextSQL, \
    SQL_EMPTY_STRING
from mo_json.types import JX_BOOLEAN, JX_TEXT


class MissingOp(MissingOp_):
    @check
    def to_sql(self, schema):
        sql = self.expr.partial_eval(SQLang).to_sql(schema)

        if is_op(sql.miss, MissingOp):
            if sql.type == JX_TEXT:
                return SqlScript(
                    data_type=JX_BOOLEAN,
                    miss=FALSE,
                    expr=sql_iso(
                        sql.frum,
                        SQL_IS_NULL,
                        SQL_OR,
                        sql_iso(sql.frum),
                        SQL_EQ,
                        SQL_EMPTY_STRING
                    ),
                    frum=self,
                    schema=schema
                )

            return SqlScript(
                data_type=JX_BOOLEAN,
                miss=FALSE,
                expr=ConcatSQL(sql.frum, SQL_IS_NULL),
                frum=self,
                schema=schema
            )

        expr = sql.miss.to_sql(schema)
        return SqlScript(data_type=JX_BOOLEAN, miss=FALSE, expr=expr, frum=sql.miss, schema=schema)
