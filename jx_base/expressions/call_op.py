# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from mo_dots import to_data

from jx_base.expressions.expression import Expression
from mo_json.types import JX_TEXT


class CallOp(Expression):
    _data_type = JX_TEXT

    def __init__(self, func, *args, **kwargs):
        Expression.__init__(self, *[func, *args, *(v for v in kwargs.values())])
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def vars(self):
        output = self.func.vars()
        for a in self.args:
            output.extend(a.vars())
        for v in self.kwargs.values():
            output.extend(v.vars())
        return output

    def map(self, map_):
        return CallOp(
            self.func.map(map_),
            tuple(v.map(map_) for v in self.args),
            {k: v.map(map_) for k, v in self.kwargs.items()},
        )

    def partial_eval(self, lang):
        func = self.func.partial_eval(lang)
        args = [a.partial_eval(lang) for a in self.args]
        kwargs = {k: v.partial_eval(lang) for k, v in self.kwargs}
        return CallOp(func, *args, **kwargs)

    def __data__(self):
        return to_data({
            "call": self.func.__data__(),
            "args": [a.__data__() for a in self.args],
            "kwargs": {k: v.__data__() for k, v in self.kwargs},
        })
