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
from jx_base.expressions.literal import ZERO
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.true_op import TrueOp
from jx_base.expressions.tuple_op import TupleOp
from mo_dots import is_many
from mo_json.types import JX_INTEGER


class CountOp(Expression):
    has_simple_form = False
    _data_type = JX_INTEGER

    def __init__(self, terms, default=ZERO, **clauses):
        Expression.__init__(self, terms)
        if is_many(terms):
            # SHORTCUT: ASSUME AN ARRAY OF IS A TUPLE
            self.terms = TupleOp(terms)
        else:
            self.terms = terms
        self.default = default

    def __data__(self):
        return {"count": self.terms.__data__(), "default": self.default.__data__()}

    def vars(self):
        return self.terms.vars()

    def map(self, map_):
        return CountOp(self.terms.map(map_))

    def missing(self, lang):
        return FALSE

    def exists(self):
        return TrueOp
