# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from mo_logs import Log
from mo_times import Date

from jx_base.expressions.case_op import CaseOp
from jx_base.expressions.coalesce_op import CoalesceOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.first_op import FirstOp
from jx_base.expressions.literal import Literal, ZERO, ONE
from jx_base.expressions.literal import is_literal
from jx_base.expressions.null_op import NULL
from jx_base.expressions.select_op import SelectOp
from jx_base.expressions.true_op import TRUE
from jx_base.expressions.when_op import WhenOp
from jx_base.language import is_op
from mo_imports import export
from mo_json.types import JX_NUMBER, base_type


class ToNumberOp(Expression):
    _data_type = JX_NUMBER

    def __init__(self, term):
        Expression.__init__(self, term)
        self.term = term

    def __data__(self):
        return {"number": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return ToNumberOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        term = FirstOp(self.term).partial_eval(lang)

        if is_literal(term):
            if term is NULL:
                return NULL
            elif term is FALSE:
                return ZERO
            elif term is TRUE:
                return ONE

            v = term.value
            if isinstance(v, (str, Date)):
                return Literal(float(v))
            elif isinstance(v, (int, float)):
                return term
            else:
                Log.error("can not convert {{value|json}} to number", value=term.value)
        elif base_type(term.type) == JX_NUMBER:
            return term
        elif is_op(term, CaseOp):  # REWRITING
            return CaseOp(
                [WhenOp(t.when, then=ToNumberOp(t.then)) for t in term.whens[:-1]] + [ToNumberOp(term.whens[-1])]
            ).partial_eval(lang)
        elif is_op(term, WhenOp):  # REWRITING
            return WhenOp(term.when, then=ToNumberOp(term.then), **{"else": ToNumberOp(term.els_)}).partial_eval(lang)
        elif is_op(term, CoalesceOp):
            return CoalesceOp(*(ToNumberOp(t) for t in term.terms))
        elif is_op(term, SelectOp):
            return CoalesceOp([ToNumberOp(s["value"]).partial_eval(lang) for s in term.terms])
        return ToNumberOp(term)


export("jx_base.expressions.base_multi_op", ToNumberOp)
