# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import re

from jx_base.expressions._utils import TYPE_CHECK, jx_expression
from jx_base.expressions.case_op import CaseOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import Literal, is_literal
from jx_base.expressions.reg_exp_op import RegExpOp
from jx_base.expressions.true_op import TRUE
from jx_base.expressions.variable import Variable
from jx_base.expressions.when_op import WhenOp
from jx_base.language import is_op
from mo_dots import coalesce
from mo_dots import is_data, is_missing
from mo_future import first
from mo_json.types import JX_BOOLEAN, STRING
from mo_logs import Log


class SuffixOp(Expression):
    has_simple_form = True
    _data_type = JX_BOOLEAN

    def __init__(self, expr, suffix):
        Expression.__init__(self, expr, suffix)
        self.expr = expr
        self.suffix = suffix

    @classmethod
    def define(cls, expr):
        op, param = first(expr.items())
        if TYPE_CHECK:
            if op not in ["suffix", "postfix"]:
                Log.error("expecting prefix or postfix")
        if not param:
            return TRUE
        elif is_data(param):
            kv_pair = first(param.items())
            if kv_pair:
                expr, const = first(param.items())
                return SuffixOp(Variable(expr), Literal(const))
            else:
                return TRUE
        else:
            expr, const = param
            return SuffixOp(jx_expression(expr), jx_expression(const))

    def __data__(self):
        if self.expr is None:
            return {"suffix": {}}
        elif is_op(self.expr, Variable) and is_literal(self.suffix):
            return {"suffix": {self.expr.var: self.suffix.value}}
        else:
            return {"suffix": [self.expr.__data__(), self.suffix.__data__()]}

    def __call__(self, row, rownum=None, rows=None):
        expr = self.expr(row, rownum, rows)
        if is_missing(expr):
            return None
        suffix = self.suffix(row, rownum, rows)
        if is_missing(suffix):
            return None
        return expr.endswith(suffix)

    def missing(self, lang):
        """
        THERE IS PLENTY OF OPPORTUNITY TO SIMPLIFY missing EXPRESSIONS
        OVERRIDE THIS METHOD TO SIMPLIFY
        :return:
        """
        return FALSE

    def vars(self):
        if self.expr is None:
            return set()
        return self.expr.vars() | self.suffix.vars()

    def map(self, map_):
        if self.expr is None:
            return TRUE
        else:
            return SuffixOp(self.expr.map(map_), self.suffix.map(map_))

    def partial_eval(self, lang):
        if self.expr is None:
            return TRUE
        if not is_literal(self.suffix) and self.suffix.type == STRING:
            Log.error("can only hanlde literal suffix ")

        return CaseOp(
            WhenOp(self.expr.missing(lang), then=FALSE),
            WhenOp(self.suffix.missing(lang), then=TRUE),
            RegExpOp(self.expr, Literal(".*" + re.escape(coalesce(self.suffix.value, ""))),),
        ).partial_eval(lang)
