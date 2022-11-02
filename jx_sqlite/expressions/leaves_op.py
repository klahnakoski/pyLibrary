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

from jx_base.expressions import LeavesOp as LeavesOp_, NULL
from jx_base.expressions.select_op import SelectOp
from jx_base.language import is_op
from jx_sqlite.expressions._utils import check, SQLang
from jx_sqlite.expressions.variable import Variable
from mo_dots import literal_field
from mo_logs import Log


class LeavesOp(LeavesOp_):
    @check
    def to_sql(self, schema):
        if not is_op(self.term, Variable):
            Log.error("Can only handle Variable")

        flat = SelectOp(schema, *[
            {
                "name": literal_field(r),
                "value": Variable(c.es_column),
                "aggregate": NULL
            }
            for r, c in schema.leaves(self.term.var)
        ])

        return flat.partial_eval(SQLang).to_sql(schema)
