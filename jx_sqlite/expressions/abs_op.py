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

from jx_base.expressions.is_number_op import IsNumberOp

from jx_base.expressions import AbsOp as AbsOp_, TRUE
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import SQL_NULL
from jx_sqlite.sqlite import sql_call
from mo_json import JX_IS_NULL, JX_NUMBER


class AbsOp(AbsOp_):
    @check
    def to_sql(self, schema):
        expr = IsNumberOp(self.term).partial_eval(SQLang).to_sql(schema)
        if not expr:
            return SqlScript(
                expr=SQL_NULL, data_type=JX_IS_NULL, frum=self, miss=TRUE, schema=schema,
            )

        return SqlScript(
            expr=sql_call("ABS", expr), data_type=JX_NUMBER, frum=self, schema=schema,
        )
