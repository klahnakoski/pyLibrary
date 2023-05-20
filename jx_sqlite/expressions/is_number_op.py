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

from jx_base.expressions import IsNumberOp as IsNumberOp_, NULL
from jx_sqlite.expressions._utils import check
from mo_json.types import JX_NUMBER


class IsNumberOp(IsNumberOp_):
    @check
    def to_sql(self, schema):
        value = self.term.to_sql(schema)
        if value._data_type == JX_NUMBER:
            return value
        else:
            return NULL.to_sql(schema)
