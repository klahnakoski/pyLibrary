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
from jx_base.expressions.literal import is_literal
from jx_base.expressions.null_op import NULL
from mo_json import OBJECT
from mo_logs import Log


class LeavesOp(Expression):
    date_type = OBJECT

    def __init__(self, *term, prefix=None):

        if prefix == None or prefix is NULL:
            prefix = NULL
        elif not is_literal(prefix):
            Log.error("expecting literal prefix")

        Expression.__init__(self, *term)
        self.term = term
        self.prefix = prefix

    def __data__(self):
        if self.prefix is not NULL:
            return {"leaves": self.term.__data__(), "prefix": self.prefix}
        else:
            return {"leaves": self.term.__data__()}

    def vars(self):
        return self.term.vars()

    def map(self, map_):
        return LeavesOp(self.term.map(map_))

    def missing(self, lang):
        return FALSE
