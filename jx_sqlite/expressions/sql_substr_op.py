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

from jx_base.expressions import NULL, SqlSubstrOp as SqlSubstrOp_
from jx_sqlite.expressions._utils import check, SQLang, OrOp
from jx_sqlite.expressions.literal import Literal
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import sql_call
from mo_json import JX_TEXT


class SqlSubstrOp(SqlSubstrOp_):
    @check
    def to_sql(self, schema):
        value = self.value.partial_eval(SQLang).to_sql(schema)
        start = self.start.partial_eval(SQLang).to_sql(schema)
        if self.length is NULL:
            sql = sql_call("SUBSTR", value, start)
        else:
            length = self.length.partial_eval(SQLang).to_sql(schema)
            sql = sql_call("SUBSTR", value, start, length)
        return SqlScript(
            data_type=JX_TEXT,
            expr=sql,
            frum=self,
            miss=OrOp([value.miss, start.miss]),
            schema=schema,
        )

    def partial_eval(self, lang):
        value = self.value.partial_eval(SQLang)
        start = self.start.partial_eval(SQLang)
        length = self.length.partial_eval(SQLang)
        if isinstance(start, Literal) and start.value == 1:
            if length is NULL:
                return value
        return SqlSubstrOp([value, start, length])
