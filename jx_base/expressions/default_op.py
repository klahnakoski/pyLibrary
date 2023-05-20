# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import is_missing, exists

from jx_base.expressions.false_op import FALSE

from jx_base.expressions.literal import TRUE

from jx_base.expressions.and_op import AndOp
from jx_base.expressions.expression import Expression
from jx_base.language import is_op
from mo_json import union_type


class DefaultOp(Expression):
    has_simple_form = True

    def __init__(self, frum, default):
        Expression.__init__(self, frum, default)
        self.frum, self.default = frum, default

    def __data__(self):
        return {"default": [self.frum.__data__(), self.default.__data__()]}

    def __eq__(self, other):
        if is_op(other, DefaultOp):
            return self.frum == other.frum and self.default == other.default
        return False

    def __call__(self, row=None, rownum=None, rows=None):
        frum = self.frum(row, rownum, rows)
        if exists(frum):
            return frum
        return self.default(row, rownum, rows)

    @property
    def type(self):
        return union_type(self.frum.type, self.default.type)

    def missing(self, lang):
        return AndOp(self.frum.missing(), self.default.missing())

    def vars(self):
        return self.frum.vars() | self.default.vars()

    def map(self, map_):
        return DefaultOp(self.frum.map(map_), self.default.map(map_))

    def partial_eval(self, lang):
        frum = self.frum.partial_eval(lang)
        frum_miss = frum.missing(lang)
        if frum_miss is TRUE:
            return self.default.partial_eval(lang)
        if frum_miss is FALSE:
            return frum

        default = self.default.partial_eval(lang)
        fall_miss = default.missing(lang)
        if fall_miss is TRUE:
            return frum
        return DefaultOp(self.frum.partial_eval(lang), self.default.partial_eval(lang))
