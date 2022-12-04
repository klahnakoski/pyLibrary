# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import absolute_import, division, unicode_literals

from jx_base.expressions.case_op import CaseOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.last_op import LastOp
from jx_base.expressions.literal import is_literal, Literal
from jx_base.language import is_op
from mo_dots import is_many
from mo_future import first
from mo_imports import expect
from mo_json.types import base_type, T_ARRAY

WhenOp = expect("WhenOp")


class FirstOp(Expression):
    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term
        self._data_type = self.term.type

    def __data__(self):
        return {"first": self.term.__data__()}

    def __call__(self, row, rownum=None, rows=None):
        value = self.term(row, rownum, rows)
        if is_many(value):
            return first(value)
        else:
            return value

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return LastOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        term = self.term.partial_eval(lang)

        if base_type(term.type) != T_ARRAY:
            return term
        elif is_op(term, FirstOp):
            return term
        elif is_op(term, CaseOp):  # REWRITING
            return CaseOp(
                [WhenOp(t.when, then=FirstOp(t.then)) for t in term.whens[:-1]]
                + [FirstOp(term.whens[-1])]
            ).partial_eval(lang)
        elif is_op(term, WhenOp):
            return WhenOp(
                term.when, then=FirstOp(term.then), **{"else": FirstOp(term.els_)}
            ).partial_eval(lang)
        elif base_type(term.type) == T_ARRAY:
            return term
        elif is_literal(term):
            value = term.value
            if is_many(value):
                return Literal(first(value))
            else:
                return Literal(value)
        else:
            return FirstOp(term)
