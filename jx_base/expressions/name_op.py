# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_logs import logger

from jx_base.expressions.expression import Expression
from jx_base.expressions.literal import is_literal
from mo_json import JxType


class NameOp(Expression):
    """
    Attach a name to value, or structure
    """

    def __init__(self, frum, name):
        if not is_literal(name):
            logger.error("expecting a literal name")
        Expression.__init__(self, frum, name)
        self._name = name
        self.frum = frum

    def __data__(self):
        return {"name": [self.frum.__data(), self._name.__data__()]}

    def vars(self):
        return self.frum.vars() | self._name.vars()

    def map(self, map_):
        return NameOp(self.frum.map(map_), self._name.map(map_))

    @property
    def type(self):
        return JxType(**{self._name.value: self.frum.type})

    def missing(self, lang):
        return self.frum.missing(lang)
