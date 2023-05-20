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
from jx_base.expressions.literal import is_literal
from jx_base.expressions.null_op import NULL
from jx_base.language import is_op
from mo_dots import last, is_many
from mo_json import OBJECT, jx_type_to_json_type


class LastOp(Expression):
    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term
        self._data_type = self.term.type

    def __data__(self):
        return {"last": self.term.__data__()}

    def __call__(self, row, rownum=None, rows=None):
        value = self.term(row, rownum, rows)
        if is_many(value):
            if isinstance(value, (list, tuple)):
                return value[-1]
            else:
                raise NotImplementedError()

        return value

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return LastOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)
        if is_op(self.term, LastOp):
            return term
        elif term is NULL:
            return term
        elif is_literal(term):
            return last(term)
        else:
            return LastOp(term)
