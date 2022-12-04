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

from jx_base.expressions import ToIntegerOp as IntegerOp_
from jx_sqlite.expressions._utils import check, SqlScript
from jx_sqlite.sqlite import sql_cast
from mo_json import base_type, T_TEXT, T_INTEGER


class ToIntegerOp(IntegerOp_):
    @check
    def to_sql(self, schema):
        value = self.term.to_sql(schema)

        if base_type(value) == T_TEXT:
            return SqlScript(
                data_type=T_INTEGER,
                expr=sql_cast(value, "INTEGER"),
                frum=self,
                miss=value.miss,
                schea=schema,
            )
        return value
