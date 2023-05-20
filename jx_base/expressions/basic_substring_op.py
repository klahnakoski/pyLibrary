# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from mo_json.types import JX_TEXT


class BasicSubstringOp(Expression):
    """
    PLACEHOLDER FOR BASIC value.substring(start, end) (CAN NOT DEAL WITH NULLS)
    """

    _data_type = JX_TEXT

    def __init__(self, *terms):
        Expression.__init__(self, *terms)
        self.value, self.start, self.end = terms

    def __data__(self):
        return {"basic.substring": [self.value.__data__(), self.start.__data__(), self.end.__data__()]}

    def map(self, map_):
        return BasicSubstringOp(self.value.map(map_), self.start.map(map_), self.end.map(map_),)

    def vars(self):
        return self.value.vars() | self.start.vars() | self.end.vars()

    def missing(self, lang):
        return FALSE

    def invert(self, lang):
        return FALSE
