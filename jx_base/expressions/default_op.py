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

from jx_base.expressions.and_op import AndOp
from jx_base.expressions.expression import Expression
from jx_base.language import is_op
from mo_json import union_type


class DefaultOp(Expression):
    has_simple_form = True

    def __init__(self, *terms):
        Expression.__init__(self, terms)
        self.expr, self.default = terms
        self._data_type = union_type(*(t.type for t in terms))

    def __data__(self):
        return {"default": [self.expr.__data__(), self.default.__data__()]}

    def __eq__(self, other):
        if is_op(other, DefaultOp):
            return self.expr == other.frum and self.default == other.default
        return False

    def missing(self, lang):
        return AndOp([self.expr.missing(), self.default.missing()])

    def vars(self):
        return self.expr.vars() | self.default.vars()

    def map(self, map_):
        return DefaultOp([self.expr.map(map_), self.default.map(map_)])

    def partial_eval(self, lang):
        expr_miss = self.expr.missing()
        if expr_miss is TRUE:
            return self.default.partial_eval(lang)
        if expr_miss is FALSE:
            return self.expr.partial_eval(lang)

        fall_miss = self.default.missing()
        if fall_miss is TRUE:
            return self.expr.partial_eval(lang)
        return DefaultOp([self.expr.partial_eval(lang), self.default.partial_eval(lang)])
