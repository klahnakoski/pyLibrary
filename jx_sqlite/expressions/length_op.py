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
    LengthOp as LengthOp_,
    is_literal,
    ToBooleanOp,
    IsTextOp,
)
from jx_sqlite.expressions._utils import SQLang, check, SqlScript
from jx_sqlite.sqlite import quote_value, sql_call, SQL_NULL
from mo_future import text
from mo_json import T_INTEGER


class LengthOp(LengthOp_):
    @check
    def to_sql(self, schema):
        term = self.term.partial_eval(SQLang)
        if is_literal(term):
            val = term.value
            if isinstance(val, text):
                if not val:
                    sql = SQL_NULL
                else:
                    sql = quote_value(len(val))
            else:
                return SQL_NULL
        else:
            value = term.to_sql(schema)
            sql = sql_call("LENGTH", value.frum)
        return SqlScript(
            data_type=T_INTEGER,
            expr=sql,
            frum=self,
            miss=ToBooleanOp(IsTextOp(self.term)),
            schema=schema,
        )
