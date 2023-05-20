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
    NotLeftOp as NotLeftOp_,
    GteOp,
    LengthOp,
    AddOp,
    MaxOp,
    ZERO,
    ONE,
)
from jx_sqlite.expressions._utils import check, SQLang, SqlScript, OrOp
from jx_sqlite.sqlite import sql_call, SQL_ZERO, ConcatSQL, SQL_ONE, SQL_PLUS
from mo_json import JX_TEXT


class NotLeftOp(NotLeftOp_):
    @check
    def to_sql(self, schema):
        v = self.value.to_sql(schema)
        start = (
            AddOp([MaxOp([ZERO, self.length]), ONE]).partial_eval(SQLang).to_sql(schema)
        )

        expr = sql_call("SUBSTR", v, start)
        return SqlScript(
            data_type=JX_TEXT,
            expr=expr,
            frum=self,
            miss=OrOp([
                self.value.missing(SQLang),
                self.length.missing(SQLang),
                GteOp([self.length, LengthOp(self.value)]),
            ]),
            schema=schema,
        )
