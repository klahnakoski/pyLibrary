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

from jx_base.expressions import MaxOp as MaxOp_, MissingOp
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import sql_call
from mo_json import JX_NUMBER


class MaxOp(MaxOp_):
    @check
    def to_sql(self, schema):
        miss = MissingOp(self).partial_eval(SQLang)
        expr = sql_call("MAX", *(t.to_sql(schema) for t in self.terms))
        return SqlScript(
            data_type=JX_NUMBER, miss=miss, expr=expr, frum=self, schema=schema
        )
