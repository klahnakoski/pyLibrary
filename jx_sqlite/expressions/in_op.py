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
    InOp as InOp_,
    FALSE,
    FalseOp,
    NestedOp,
    Variable,
    EqOp,
    ExistsOp,
)
from jx_base.language import is_op
from jx_sqlite.expressions._utils import SQLang, check, SqlScript
from jx_sqlite.expressions.literal import Literal
from jx_sqlite.sqlite import SQL_FALSE, SQL_IN, ConcatSQL
from jx_sqlite.sqlite import quote_list
from mo_json import T_BOOLEAN
from mo_logs import Log


class InOp(InOp_):
    @check
    def to_sql(self, schema):
        value = self.value.partial_eval(SQLang).to_sql(schema)
        superset = self.superset.partial_eval(SQLang)
        if is_op(superset, Literal):
            values = superset.value
            if value._data_type == T_BOOLEAN:
                values = [value2boolean(v) for v in values]
            # TODO: DUE TO LIMITED BOOLEANS, TURN THIS INTO EqOp
            sql = ConcatSQL(value, SQL_IN, quote_list(values))
            return SqlScript(
                data_type=T_BOOLEAN, expr=sql, frum=self, miss=FALSE, schema=schema
            )

        if not is_op(superset, Variable):
            Log.error("Do not know how to hanldle")

        sub_table = schema.get_table(superset.var)
        return ExistsOp(NestedOp(
            nested_path=sub_table.nested_path, where=EqOp([Variable("."), value.frum])
        )).to_sql(schema)
