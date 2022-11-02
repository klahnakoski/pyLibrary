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

from jx_base.expressions import NotOp as NotOp_, BasicNotOp
from jx_base.language import is_op
from jx_sqlite.expressions._utils import check, SQLang, OrOp


class NotOp(NotOp_):
    @check
    def to_sql(self, schema):
        term = self.partial_eval(SQLang)
        if is_op(term, NotOp):
            return OrOp([term.term.missing(SQLang), BasicNotOp(term.term)]).partial_eval(SQLang).to_sql(schema)
        else:
            return term.to_sql(schema)
