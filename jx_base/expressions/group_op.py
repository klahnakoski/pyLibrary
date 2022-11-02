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


class GroupOp(Expression):
    def __init__(self, *terms):
        Expression.__init__(self, terms)
        self.frum, self.select = terms
        if self.frum.type != T_ARRAY:
            Log.error("expecting an array")

    def __data__(self):
        return {"group": [self.frum.__data(), self.select.__data__()]}

    def vars(self):
        return self.frum.vars() | self.select.vars()

    def map(self, map_):
        return GroupOp([self.frum.map(map_), self.select.map(map_)])

    @property
    def type(self):
        return self.frum.type

    def missing(self, lang):
        return MissingOp(self)

    def invert(self, lang):
        return self.missing(lang)
