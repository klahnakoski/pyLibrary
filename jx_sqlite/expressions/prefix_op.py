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

from jx_base.expressions import PrefixOp as PrefixOp_
from jx_sqlite.expressions._utils import check, SQLang
from jx_sqlite.sqlite import sql_call
from mo_dots import wrap
from jx_sqlite.sqlite import SQL_TRUE, ConcatSQL, SQL_EQ, SQL_ONE


class PrefixOp(PrefixOp_):
    @check
    def to_sql(self, schema):
        if not self.expr:
            return wrap([{"name": ".", "sql": {"b": SQL_TRUE}}])
        else:
            sql = ConcatSQL(
                sql_call(
                    "INSTR",
                    self.expr.partial_eval(SQLang).to_sql(schema),
                    self.prefix.partial_eval(SQLang).to_sql(schema),
                ),
                SQL_EQ,
                SQL_ONE,
            )
            return wrap([{"name": ".", "sql": {"b": sql}}])
