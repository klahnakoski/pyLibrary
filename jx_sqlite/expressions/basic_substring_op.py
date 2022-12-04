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

from jx_base.expressions import BasicSubstringOp as BasicSubstringOp_, FALSE
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.expressions.add_op import AddOp
from jx_sqlite.expressions.literal import Literal
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.expressions.sub_op import SubOp
from jx_sqlite.sqlite import sql_call
from mo_json import T_TEXT


class BasicSubstringOp(BasicSubstringOp_):
    @check
    def to_sql(self, schema):
        value = self.value.partial_eval(SQLang).to_sql(schema)
        start = AddOp([self.start, Literal(1)]).partial_eval(SQLang).to_sql(schema)
        length = SubOp([self.end, self.start]).partial_eval(SQLang).to_sql(schema)
        sql = sql_call("SUBSTR", value.frum, start.frum, length.frum)
        return SqlScript(
            data_type=T_TEXT, expr=sql, frum=self, miss=FALSE, schema=schema
        )
