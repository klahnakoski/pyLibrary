# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions._utils import _jx_expression
from jx_base.expressions.expression import Expression
from jx_base.language import JX


class CommentOp(Expression):
    def __init__(self, frum, commment):
        Expression.__init__(self, frum, comment)
        self.frum = frum
        self.comment = comment

    @classmethod
    def define(cls, expr):
        items = list(expr.items())
        if len(items) != 1:
            Log.error("expecting comment")
        op, params = items[0]
        if op not in ["comment", "description", "meta"]:
            Log.error("expecting comment")
        return _jx_expression(params[0], cls.lang)

    def __data__(self):
        return {"comment": [self.frum.__data(), self.comment.__data__()]}

    def vars(self):
        return self.frum.vars() | self.comment.vars()

    def map(self, map_):
        return CommentOp(self.frum.map(mao_), self.comment.map(map_))

    @property
    def type(self):
        return self.frum.type
