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
    BasicStartsWithOp as BasicStartsWithOp_,
    is_literal,
    FALSE,
)
from jx_sqlite.expressions._utils import SQLang, check, SqlScript
from jx_sqlite.expressions.sql_eq_op import SqlEqOp
from jx_sqlite.expressions.sql_instr_op import SqlInstrOp
from jx_sqlite.sqlite import SQL, ConcatSQL, SQL_LIKE, SQL_ESCAPE, SQL_ONE
from jx_sqlite.sqlite import quote_value
from mo_json.types import JX_BOOLEAN


class BasicStartsWithOp(BasicStartsWithOp_):
    @check
    def to_sql(self, schema):
        prefix = self.prefix.partial_eval(SQLang)
        if is_literal(prefix):
            value = self.value.partial_eval(SQLang).to_sql(schema)
            prefix = prefix.value
            if "%" in prefix or "_" in prefix:
                for r in "\\_%":
                    prefix = prefix.replaceAll(r, "\\" + r)
                sql = ConcatSQL(
                    value, SQL_LIKE, quote_value(prefix + "%"), SQL_ESCAPE, SQL("\\")
                )
            else:
                sql = ConcatSQL(value, SQL_LIKE, quote_value(prefix + "%"))
            return SqlScript(
                data_type=JX_BOOLEAN, expr=sql, frum=self, miss=FALSE, schema=schema
            )
        else:
            return (
                SqlEqOp([SqlInstrOp([self.value, prefix]), SQL_ONE])
                .partial_eval(SQLang)
                .to_sql()
            )
