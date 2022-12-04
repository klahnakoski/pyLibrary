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

from jx_base.expressions.expression import Expression
from jx_base.expressions.null_op import NULL


class ToArrayOp(Expression):

    def __init__(self, *term):
        Expression.__init__(self, [term])
        self.term = term

    def __data__(self):
        return {"array": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return ToArrayOp(self.term.map(map_))

    def missing(self, lang):
        return self.term.missing(lang)

    def partial_eval(self, lang):
        if self.term.missing():
            return NULL
        if self.term.type == T_ARRAY:
            return self.term.partial_eval(lang)
        return ToArrayOp(self.term.partial_eval(lang))
