# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from dataclasses import dataclass
from typing import Dict, Tuple, List

from jx_base.expressions._utils import TYPE_CHECK
from jx_base.expressions.expression import Expression
from mo_json import JxType
from mo_logs import Log


@dataclass
class Source:
    alias: str
    frum: Expression
    joins: List


@dataclass
class Join:
    ones_table: Source
    ones_columns: List[str]
    many_table: Source
    many_columns: List[str]


class SqlLeftJoinsOp(Expression):
    def __init__(self, frum: Source, selects: Tuple[Dict[str, Expression]]):
        if TYPE_CHECK and (
            not isinstance(selects, tuple)
            and not all(isinstance(s, dict) for s in selects[1:])
            or any(s.get("name") is None for s in selects)
        ):
            Log.error("expecting list of dicts with 'name' and 'value' property")
        Expression.__init__(self)
        self.frum = frum
        self.selects = selects  # REQUIRED FOR type

    @property
    def type(self):
        return JxType(**{s["name"]: s["value"] for s in self.selects})

