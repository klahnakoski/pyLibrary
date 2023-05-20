# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions._utils import _jx_expression
from jx_base.expressions.and_op import AndOp
from jx_base.expressions.basic_eq_op import BasicEqOp
from jx_base.expressions.case_op import CaseOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import is_literal, Literal
from jx_base.expressions.true_op import TRUE
from jx_base.expressions.variable import Variable
from jx_base.language import JX
from jx_base.language import is_op, value_compare
from mo_dots import is_many, is_data
from mo_imports import expect
from mo_imports import export
from mo_json.types import JX_BOOLEAN

InOp, WhenOp = expect("InOp", "WhenOp")


class EqOp(Expression):
    has_simple_form = True
    _data_type = JX_BOOLEAN

    def __new__(cls, *terms):
        if is_many(terms):
            return object.__new__(cls)

        items = terms.items()
        if len(items) == 1:
            if is_many(items[0][1]):
                return InOp(items[0])
            else:
                return EqOp(items[0])
        else:
            acc = []
            for lhs, rhs in items:
                if rhs.json.startswith("["):
                    acc.append(InOp(Variable(lhs), rhs))
                else:
                    acc.append(EqOp(Variable(lhs), rhs))
            return AndOp(acc)

    @classmethod
    def define(cls, expr):
        items = list(expr.items())
        if len(items) != 1:
            Log.error("expecting single property")
        op, terms = items[0]
        if op != "eq":
            Log.error("Expecting eq op")
        if is_many(terms):
            return EqOp(*(_jx_expression(e, cls.lang) for e in terms))
        elif is_data(terms):
            items = list(terms.items())
            if len(items) == 1:
                lhs, rhs = items[0]
                return EqOp(Variable(lhs), Literal(rhs))
            else:
                return AndOp(*(EqOp(Variable(lhs), Literal(rhs)) for lhs, rhs in items))
        else:
            Log.error("do not not know what to do")

    def __init__(self, lhs, rhs):
        Expression.__init__(self, lhs, rhs)
        self.lhs, self.rhs = lhs, rhs

    def __data__(self):
        if is_op(self.lhs, Variable) and is_literal(self.rhs):
            return {"eq": {self.lhs.var: self.rhs.value}}
        else:
            return {"eq": [self.lhs.__data__(), self.rhs.__data__()]}

    def __call__(self, row, rownum=None, rows=None):
        return self.lhs(row, rownum, rows) == self.rhs(row, rownum, rows)

    def __eq__(self, other):
        if is_op(other, EqOp):
            return self.lhs == other.lhs and self.rhs == other.rhs
        return False

    def vars(self):
        return self.lhs.vars() | self.rhs.vars()

    def map(self, map_):
        return EqOp(self.lhs.map(map_), self.rhs.map(map_))

    def missing(self, lang):
        return FALSE

    def exists(self):
        return TRUE

    def partial_eval(self, lang):
        lhs = self.lhs.partial_eval(lang)
        rhs = self.rhs.partial_eval(lang)

        if is_literal(lhs) and is_literal(rhs):
            return FALSE if value_compare(lhs.value, rhs.value) else TRUE
        else:
            return CaseOp(
                WhenOp(lhs.missing(lang), then=rhs.missing(lang)),
                WhenOp(rhs.missing(lang), then=FALSE),
                BasicEqOp(lhs, rhs),
            ).partial_eval(lang)


export("jx_base.expressions.basic_in_op", EqOp)
