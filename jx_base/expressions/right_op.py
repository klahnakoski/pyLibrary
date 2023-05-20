# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.basic_substring_op import BasicSubstringOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.length_op import LengthOp
from jx_base.expressions.literal import ZERO
from jx_base.expressions.literal import is_literal
from jx_base.expressions.max_op import MaxOp
from jx_base.expressions.min_op import MinOp
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.sub_op import SubOp
from jx_base.expressions.variable import Variable
from jx_base.expressions.when_op import WhenOp
from jx_base.language import is_op
from mo_json.types import JX_TEXT


class RightOp(Expression):
    has_simple_form = True
    _data_type = JX_TEXT

    def __init__(self, value, length):
        Expression.__init__(self, value, length)
        self.value, self.length = value, length

    def __data__(self):
        if is_op(self.value, Variable) and is_literal(self.length):
            return {"right": {self.value.var: self.length.value}}
        else:
            return {"right": [self.value.__data__(), self.length.__data__()]}

    def vars(self):
        return self.value.vars() | self.length.vars()

    def map(self, map_):
        return RightOp(self.value.map(map_), self.length.map(map_))

    def missing(self, lang):
        return OrOp(self.value.missing(lang), self.length.missing(lang))

    def partial_eval(self, lang):
        value = self.value.partial_eval(lang)
        length = self.length.partial_eval(lang)
        max_length = LengthOp(value).partial_eval(lang)

        return WhenOp(
            self.missing(lang),
            **{"else": BasicSubstringOp(value, MaxOp(ZERO, MinOp(max_length, SubOp(max_length, length))), max_length,)}
        ).partial_eval(lang)
