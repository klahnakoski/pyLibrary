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

from jx_base.expressions import OrOp as OrOp_
from jx_base.expressions.false_op import FALSE
from jx_sqlite.expressions._utils import SQLang, check
from jx_sqlite.sqlite import SQL_OR, sql_iso, JoinSQL
from mo_imports import export, expect
from mo_json import T_BOOLEAN

SqlScript = expect("SqlScript")


class OrOp(OrOp_):
    @check
    def to_sql(self, schema):
        return SqlScript(
            data_type=T_BOOLEAN,
            miss=FALSE,
            expr=JoinSQL(
                SQL_OR,
                [sql_iso(t.partial_eval(SQLang).to_sql(schema)) for t in self.terms],
            ),
            frum=self,
            schema=schema
        )


export("jx_sqlite.expressions._utils", OrOp)
