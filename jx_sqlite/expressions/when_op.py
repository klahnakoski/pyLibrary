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

from jx_base.expressions import WhenOp as WhenOp_, ToBooleanOp, TRUE, NotOp, AndOp
from jx_sqlite.expressions._utils import SQLang, check, SqlScript, OrOp
from jx_sqlite.sqlite import SQL_CASE, SQL_ELSE, SQL_END, SQL_THEN, SQL_WHEN, ConcatSQL


class WhenOp(WhenOp_):
    @check
    def to_sql(self, schema):
        when = ToBooleanOp(self.when).partial_eval(SQLang).to_sql(schema)
        then = self.then.partial_eval(SQLang).to_sql(schema)
        els_ = self.els_.partial_eval(SQLang).to_sql(schema)

        if then.miss is TRUE:
            return SqlScript(
                data_type=els_.type,
                frum=self,
                expr=els_.frum,
                miss=OrOp([when, els_.miss]),
                schema=schema,
            )
        elif els_.miss is TRUE:
            return SqlScript(
                data_type=then.type,
                frum=self,
                expr=then.frum,
                miss=OrOp([when.miss, NotOp(when), then.miss]),
                schema=schema,
            )

        return SqlScript(
            data_type=then.type | els_.type,
            frum=self,
            expr=ConcatSQL(
                SQL_CASE, SQL_WHEN, when.frum, SQL_THEN, then.frum, SQL_ELSE, els_.frum, SQL_END
            ),
            miss=OrOp([AndOp([when.frum, then.miss]), AndOp([OrOp([when.miss, NotOp(when.frum)]), els_.miss])]),
            schema=schema,
        )
