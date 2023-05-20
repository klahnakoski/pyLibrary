# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import is_many

from jx_base.expressions.case_op import CaseOp
from jx_base.expressions.eq_op import EqOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import is_literal, Literal, ZERO
from jx_base.expressions.min_op import MinOp
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.when_op import WhenOp
from jx_base.language import is_op
from jx_base.utils import enlist


class LimitOp(Expression):
    def __init__(self, frum, amount):
        Expression.__init__(self, frum, amount)
        self.frum = frum
        self.amount = amount
        self._data_type = self.frum.type

    def __data__(self):
        return {"limit": [self.frum.__data__(), self.amount.__data__()]}

    def __call__(self, row, rownum=None, rows=None):
        amount = self.amount(row, rownum, rows)
        if not amount:
            return []
        value = self.frum(row, rownum, rows)
        if is_many(value):
            return value[:amount]
        else:
            return value

    def vars(self):
        return self.frum.vars() | self.amount.vars()

    def map(self, map_):
        return LimitOp(self.frum.map(map_), self.amount.map(map_))

    def missing(self, lang):
        return OrOp(self.frum.missing(lang), EqOp(self.amount, ZERO))

    def partial_eval(self, lang):
        frum = self.frum.partial_eval(lang)
        amount = self.amount.partial_eval(lang)

        if is_op(frum, LimitOp):
            return LimitOp(frum.frum, MinOp(frum.amount, amount)).partial_eval(lang)
        elif is_op(frum, CaseOp):  # REWRITING
            return CaseOp(
                [WhenOp(t.when, then=LimitOp(t.then, amount)) for t in frum.whens[:-1]]
                + [LimitOp(frum.whens[-1], amount)]
            ).partial_eval(lang)
        elif is_op(frum, WhenOp):
            return WhenOp(
                frum.when, then=LimitOp(frum.then, amount), **{"else": LimitOp(frum.els_, amount)}
            ).partial_eval(lang)
        elif is_literal(frum) and is_literal(amount):
            return Literal(enlist(frum.value)[: amount.value])
        else:
            return LimitOp(frum, amount)
