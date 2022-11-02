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
from mo_imports import DelayedValue
from jx_base.expressions.expression import Expression
from mo_future import first
from jx_base.expressions.null_op import NULL


class AggregateOp(Expression):
    def __init__(self, frum, op):
        Expression.__init__(self, frum)
        if op not in canonical_aggregates:
            Log.error(f"{op} is not a known aggrewgat")

        self.frum = frum
        self.op = canonical_aggregates[op]

    def __data__(self):
        return {"aggregate": [
            self.frum.__data__(),
            first(self.op(NULL).__data__().keys()),
        ]}

    def vars(self):
        return self.frum.vars() | self.op.vars()

    def map(self, map_):
        return AggregateOp([self.frum.map(mao_), self.op.map(map_)])

    @property
    def type(self):
        # THIS CAN BE BETTER
        return self.frum.type

    def missing(self, lang):
        return self.frum.missing()

    def invert(self, lang):
        return self.missing(lang)


def canonical_aggregates():
    from jx_base.expressions.add_op import AddOp
    from jx_base.expressions.and_op import AndOp
    from jx_base.expressions.avg_op import AvgOp
    from jx_base.expressions.cardinality_op import CardinalityOp
    from jx_base.expressions.count_op import CountOp
    from jx_base.expressions.max_op import MaxOp
    from jx_base.expressions.min_op import MinOp
    from jx_base.expressions.null_op import NullOp
    from jx_base.expressions.or_op import OrOp
    from jx_base.expressions.union_op import UnionOp

    return {
        "none": NullOp,
        "cardinality": CardinalityOp,
        "count": CountOp,
        "min": MinOp,
        "minimum": MinOp,
        "max": MaxOp,
        "maximum": MaxOp,
        "add": AddOp,
        "sum": AddOp,
        "avg": AvgOp,
        "average": AvgOp,
        "mean": AvgOp,
        "and": AndOp,
        "or": OrOp,
        "union": UnionOp,
    }


canonical_aggregates = DelayedValue(canonical_aggregates)

