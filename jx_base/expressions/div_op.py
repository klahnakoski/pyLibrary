# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions._utils import builtin_ops
from jx_base.expressions.and_op import AndOp
from jx_base.expressions.base_binary_op import BaseBinaryOp
from jx_base.expressions.eq_op import EqOp
from jx_base.expressions.literal import Literal, ZERO, is_literal, NULL
from jx_base.expressions.or_op import OrOp


class DivOp(BaseBinaryOp):
    op = "div"

    def __call__(self, row=None, rownum=None, rows=None):
        lhs = self.lhs(row)
        rhs = self.rhs(row)
        if not isinstance(lhs, (float, int)) or not rhs:
            return None
        return lhs/rhs

    def missing(self, lang):
        return OrOp(self.lhs.missing(lang), self.rhs.missing(lang), EqOp(self.rhs, ZERO)).partial_eval(lang)

    def partial_eval(self, lang):
        rhs = self.rhs.partial_eval(lang)
        if rhs is ZERO:
            return NULL
        lhs = self.lhs.partial_eval(lang)
        if is_literal(lhs) and is_literal(rhs):
            return Literal(lhs.value / rhs.value)
        return DivOp(lhs, rhs)
