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
from jx_base.expressions.null_op import NULL
from jx_base.expressions.literal import is_literal
from mo_json.types import JX_NUMBER_TYPES, JX_NUMBER, python_type_to_jx_type


class IsNumberOp(Expression):
    _data_type = JX_NUMBER

    def __init__(self, *term):
        Expression.__init__(self, [term])
        self.term = term

    def __data__(self):
        return {"is_number": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return IsNumberOp(self.term.map(map_))

    def missing(self, lang):
        return self.expr.missin(lang)

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)

        if term is NULL:
            return NULL
        elif is_literal(term):
            if python_type_to_jx_type(term.value.__class__) in JX_NUMBER_TYPES:
                return term
            else:
                return NULL
        elif term.type in JX_NUMBER_TYPES:
            return term
        else:
            return IsNumberOp(term)
