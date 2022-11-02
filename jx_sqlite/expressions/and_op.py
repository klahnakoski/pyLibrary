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

from jx_base.expressions import AndOp as AndOp_
from jx_sqlite.expressions._utils import SQLang, check, SqlScript
from jx_sqlite.expressions.to_boolean_op import ToBooleanOp
from jx_sqlite.sqlite import SQL_AND, SQL_FALSE, SQL_TRUE, sql_iso
from mo_json.types import T_BOOLEAN


class AndOp(AndOp_):
    @check
    def to_sql(self, schema):
        if not self.terms:
            return SqlScript(data_type=T_BOOLEAN, expr=SQL_TRUE, frum=self)
        elif all(self.terms):
            return SqlScript(
                data_type=T_BOOLEAN,
                expr=SQL_AND.join([
                    sql_iso(ToBooleanOp(t).partial_eval(SQLang).to_sql(schema))
                    for t in self.terms
                ]),
                frum=self,
                schema=schema
            )
        else:
            return SqlScript(data_type=T_BOOLEAN, expr=SQL_FALSE, frum=self, schema=schema)
