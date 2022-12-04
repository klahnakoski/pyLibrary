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

from jx_base.expressions import ExistsOp as ExistsOp_, FALSE
from jx_sqlite.expressions._utils import check, SQLang, SqlScript
from mo_json import T_BOOLEAN


class ExistsOp(ExistsOp_):
    @check
    def to_sql(self, schema):
        sql = self.expr.partial_eval(SQLang).to_sql(schema)
        return SqlScript(
            data_type=T_BOOLEAN, expr=sql, frum=self, miss=FALSE, schema=schema
        )
