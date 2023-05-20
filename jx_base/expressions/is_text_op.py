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
from mo_json import STRING
from mo_json.types import JX_TEXT


class IsTextOp(Expression):
    _data_type = JX_TEXT

    def __init__(self, *term):
        Expression.__init__(self, [term])
        self.term = term

    def __data__(self):
        return {"is_text": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return IsTextOp(self.term.map(map_))

    def missing(self, lang):
        return self.expr.missing()

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)

        if term.type is STRING:
            return term
        else:
            return NULL
