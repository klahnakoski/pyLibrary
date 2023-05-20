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
from mo_json.types import JX_BOOLEAN


class IsBooleanOp(Expression):
    _data_type = JX_BOOLEAN

    def __init__(self, *term):
        Expression.__init__(self, [term])
        self.term = term

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        if term.type is JX_BOOLEAN:
            return term
        elif term is self.term:
            return self
        else:
            return IsBooleanOp(term)

    def __call__(self, row=None, rownum=None, rows=None):
        value = self.term(row, rownum, rows)
        if value is True:
            return True
        elif value is False:
            return False
        else:
            return None

    def __data__(self):
        return {"is_boolean": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return IsBooleanOp(self.term.map(map_))

    def missing(self, lang):
        return FALSE
