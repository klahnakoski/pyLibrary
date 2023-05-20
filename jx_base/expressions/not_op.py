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
from jx_base.language import is_op
from mo_imports import export
from mo_json.types import JX_BOOLEAN


class NotOp(Expression):
    _data_type = JX_BOOLEAN

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __data__(self):
        return {"not": self.term.__data__()}

    def __call__(self, row, rownum=None, rows=None):
        return not self.term(row, rownum, rows)

    def __eq__(self, other):
        if not is_op(other, NotOp):
            return False
        return self.term == other.term

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return NotOp(self.term.map(map_))

    def missing(self, lang):
        return (self.term).missing(lang)

    def invert(self, lang):
        return self.term.partial_eval(lang)

    def partial_eval(self, lang):
        return self.term.invert(lang)


export("jx_base.expressions.and_op", NotOp)
export("jx_base.expressions.basic_in_op", NotOp)
export("jx_base.expressions.exists_op", NotOp)
export("jx_base.expressions.expression", NotOp)
