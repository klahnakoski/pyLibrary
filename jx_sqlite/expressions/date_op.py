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

from jx_base.expressions import DateOp as DateOp_
from jx_sqlite.expressions._utils import check
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import quote_value


class DateOp(DateOp_):
    @check
    def to_sql(self, schema):
        value = self.value
        return SqlScript(data_type=self._data_type, expr=quote_value(value), frum=self, schema=schema)
