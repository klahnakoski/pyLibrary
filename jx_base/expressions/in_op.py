# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import BasicInOp
from jx_base.expressions.and_op import AndOp
from jx_base.expressions.eq_op import EqOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import Literal
from jx_base.expressions.literal import is_literal
from jx_base.expressions.missing_op import MissingOp
from jx_base.expressions.nested_op import NestedOp
from jx_base.expressions.not_op import NotOp
from jx_base.expressions.null_op import NULL
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.variable import Variable
from jx_base.language import is_op
from mo_dots import is_many
from mo_imports import export
from mo_json.types import JX_BOOLEAN


class InOp(Expression):
    has_simple_form = True
    _data_type = JX_BOOLEAN

    def __init__(self, value, superset):
        Expression.__init__(self, value, superset)
        self.value, self.superset = value, superset

    def __data__(self):
        if is_op(self.value, Variable) and is_literal(self.superset):
            return {"in": {self.value.var: self.superset.value}}
        else:
            return {"in": [self.value.__data__(), self.superset.__data__()]}

    def __call__(self, row, rownum=None, rows=None):
        value = self.value(row, rownum, rows)
        superset = self.superset(row, rownum, rows)
        return value in superset

    def __eq__(self, other):
        if is_op(other, InOp):
            return self.value == other.value and self.superset == other.superset
        return False

    def vars(self):
        return self.value.vars()

    def map(self, map_):
        return InOp(self.value.map(map_), self.superset.map(map_))

    def partial_eval(self, lang):
        value = self.value.partial_eval(lang)
        superset = self.superset.partial_eval(lang)
        if superset is NULL:
            return FALSE
        elif value is NULL:
            return FALSE
        elif is_literal(superset):
            if is_literal(value):
                return Literal(value() in enlist(superset.value))
            elif is_many(superset.value):
                return InOp(value, superset)
            else:
                return EqOp(value, superset)
        elif is_op(value, NestedOp):
            return (
                NestedOp(value.nested_path, None, AndOp(InOp(value.select, superset), value.where),)
                .exists()
                .partial_eval(lang)
            )
        else:
            return InOp(value, superset)

    def __call__(self, row, rownum=None, rows=None):
        return self.value(row) in self.superset(row)

    def missing(self, lang):
        return FALSE

    def invert(self, lang):
        this = self.partial_eval(lang)
        if is_op(this, InOp):
            inv = NotOp(BasicInOp(this.value, this.superset))
            inv.simplified = True
            return OrOp(MissingOp(this.value), inv)
        else:
            return this.invert(lang)

    def __rcontains__(self, superset):
        if (
            is_op(self.value, Variable)
            and is_op(superset, MissingOp)
            and is_op(superset.value, Variable)
            and superset.value.var == self.value.var
        ):
            return True
        return False


export("jx_base.expressions.eq_op", InOp)
