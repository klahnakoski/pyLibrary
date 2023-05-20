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

from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import FALSE, TRUE, ONE, ZERO, NULL
from jx_base.utils import coalesce


class PythonScript(Expression):
    """
    REPRESENT A Python SCRIPT
    """

    __slots__ = ("locals", "loop_depth", "miss", "_data_type", "source", "frum", "many")

    def __init__(self, locals, loop_depth, type, source, frum, miss=None, many=False):
        if isinstance(type, str):
            Log.error("expecting JX type, not code")

        if miss not in [None, NULL, FALSE, TRUE, ONE, ZERO]:
            if frum.lang != miss.lang:
                Log.error("logic error")

        Expression.__init__(self, None)
        self.locals = locals  # Python locals for compilation to real python function
        self.loop_depth = loop_depth  # number of inner loops
        self.miss = coalesce(miss, FALSE)
        self._data_type = type
        self.source = source
        self.many = many  # True if script returns multi-value
        self.frum = frum  # THE ORIGINAL EXPRESSION THAT MADE expr

    def map(self, map_):
        return self

    def __str__(self):
        return self.source
