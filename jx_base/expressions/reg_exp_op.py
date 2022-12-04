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

from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import is_literal
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.variable import Variable
from jx_base.language import is_op
from mo_json.types import T_BOOLEAN


class RegExpOp(Expression):
    has_simple_form = True
    _data_type = T_BOOLEAN

    def __init__(self, *terms):
        Expression.__init__(self, *terms)
        self.expr, self.pattern = terms

    def __data__(self):
        if is_op(self.expr, Variable) and is_literal(self.pattern):
            return {"regexp": {self.expr.var: self.pattern.value}}

        return {"regexp": [self.expr.__data__(), self.pattern.__data__()]}

    def __eq__(self, other):
        if not isinstance(other, RegExpOp):
            return False
        return self.expr == other.expr and self.pattern == other.pattern

    def vars(self):
        return self.expr.vars() | self.pattern.vars()

    def map(self, map_):
        return RegExpOp(self.expr.map(map_), self.pattern.map(map_))

    def missing(self, lang):
        return OrOp(self.expr.missing(lang), self.pattern.missing(lang))
