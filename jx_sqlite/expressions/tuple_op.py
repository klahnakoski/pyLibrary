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

from jx_base.expressions import TupleOp as TupleOp_, SelectOp, NULL
from jx_sqlite.expressions._utils import SQLang, check


class TupleOp(TupleOp_):
    @check
    def to_sql(self, schema):
        output = SelectOp(schema, *[
            {
                "name": str(i),
                "value": term,
                "aggregate": NULL
            }
            for i, term in enumerate(self.terms)
        ]).partial_eval(SQLang).to_sql(schema)
        output.frum = self
        return output
