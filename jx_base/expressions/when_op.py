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

from jx_base.expressions.and_op import AndOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import Literal
from jx_base.expressions.not_op import NotOp
from jx_base.expressions.null_op import NULL
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.to_boolean_op import ToBooleanOp
from jx_base.expressions.true_op import TRUE
from jx_base.language import is_op
from mo_imports import export
from mo_logs import Log


class WhenOp(Expression):
    def __init__(self, when, **clauses):
        Expression.__init__(self, when)

        self.when = when
        self.then = clauses.get("then", NULL)
        self.els_ = clauses.get("else", NULL)
        self._data_type = self.then.type | self.els_.type

    def __data__(self):
        return {
            "when": self.when.__data__(),
            "then": None if self.then is NULL else self.then.__data__(),
            "else": None if self.els_ is NULL else self.els_.__data__(),
        }

    def __call__(self, row, rownum=None, rows=None):
        if self.when(row, rownum, rows):
            return self.then(row, rownum, rows)
        else:
            return self.els_(row, rownum, rows)

    def vars(self):
        return self.when.vars() | self.then.vars() | self.els_.vars()

    def map(self, map_):
        return WhenOp(
            self.when.map(map_),
            then=self.then.map(map_),
            **{"else": self.els_.map(map_)}
        )

    def missing(self, lang):
        return OrOp([
            AndOp([self.when, self.then.missing(lang)]),
            AndOp([NotOp(self.when), self.els_.missing(lang)]),
        ]).partial_eval(lang)

    def invert(self, lang):
        return OrOp([
            AndOp([self.when, self.then.invert(lang)]),
            AndOp([NotOp(self.when), self.els_.invert(lang)]),
        ]).partial_eval(lang)

    def partial_eval(self, lang):
        when = ToBooleanOp(self.when).partial_eval(lang)

        if when is TRUE:
            return self.then.partial_eval(lang)
        elif when in [FALSE, NULL]:
            return self.els_.partial_eval(lang)
        elif is_op(when, Literal):
            Log.error("Expecting `when` clause to return a Boolean, or `null`")

        then = self.then.partial_eval(lang)
        els_ = self.els_.partial_eval(lang)

        if then is TRUE:
            if els_ is FALSE:
                return when
            elif els_ is TRUE:
                return TRUE
        elif then is FALSE:
            if els_ is FALSE:
                return FALSE
            elif els_ is TRUE:
                return (NotOp(when)).partial_eval(lang)

        return WhenOp(when, then=then, **{"else": els_})


export("jx_base.expressions.base_multi_op", WhenOp)
export("jx_base.expressions.case_op", WhenOp)
export("jx_base.expressions.eq_op", WhenOp)
export("jx_base.expressions.first_op", WhenOp)
