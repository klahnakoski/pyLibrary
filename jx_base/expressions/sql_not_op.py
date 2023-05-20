# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.eq_op import EqOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.language import is_op
from mo_json.types import JX_BOOLEAN


class SqlNotOp(Expression):
    _data_type = JX_BOOLEAN

    def __init__(self, *term):
        """
        EMPTY STRINGS AND `0` ARE TREATED AS FALSE
        """
        Expression.__init__(self, *term)
        self.term = term

    def __data__(self):
        return {"sql.not": self.term.__data__()}

    def __eq__(self, other):
        if not is_op(other, SqlNotOp):
            return False
        return self.term == other.term

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return NotOp(self.term.map(map_))

    def missing(self, lang):
        return FALSE

    def invert(self, lang):
        return (
            WhenOp(
                OrOp(self.term.missing(lang), BasicEqOp(self.term, ZERO)),
                *{"then": self, "else": ToBoolean(self.term)}
            )
            .term
            .partial_eval(lang)
        )

    def partial_eval(self, lang):
        return self.term.invert(lang)
