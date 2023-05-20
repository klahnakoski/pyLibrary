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
from jx_base.expressions.literal import NULL, Literal
from mo_json import ARRAY


class ToArrayOp(Expression):
    """
    Ensure the result is an array, or Null
    """

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __data__(self):
        return {"to_array": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return ToArrayOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        if term.op == ToArrayOp.op:
            return term
        if term is NULL:
            return Literal([])
        if self.term.type == ARRAY:
            return term
        return ToArrayOp(term)
