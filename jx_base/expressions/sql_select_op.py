# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from typing import Tuple

from jx_base.expressions._utils import TYPE_CHECK
from jx_base.expressions.expression import Expression
from mo_json.types import JxType
from mo_logs import Log
from collections import namedtuple


SqlAlias = namedtuple("SqlAlias", ["name", "value"])


class SqlSelectOp(Expression):
    def __init__(self, frum, selects: Tuple[SqlAlias]):
        if TYPE_CHECK and (
            not isinstance(selects, tuple)
            and not all(isinstance(s, SqlAlias) for s in selects)
            or any(s.name is None for s in selects)
            or not all(isinstance(s.value, Expression) for s in selects)
        ):
            Log.error("expecting tuple of SqlAlias")
        Expression.__init__(self, frum)
        self.frum = frum
        self.selects = selects

    @property
    def type(self):
        return JxType(**{n: v.type for n, v in self.selects})

    def __str__(self):
        return str(self.to_sql(None))
