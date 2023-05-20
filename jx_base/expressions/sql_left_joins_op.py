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

    def copy_and_replace(self, old_origin: "Source", new_origin: "Source"):
        if self is old_origin:
            return new_origin
        return Source(self.alias, self.frum, [j.copy_and_replace(self, old_origin, new_origin) for j in self.joins],)

    def __str__(self):
        return self._start_str(None)

    def _start_str(self, origin):
        if origin == self:
            return f"((({self.alias}))){self._more_str(origin)}"
        else:
            return self.alias + self._more_str(origin)

    def _more_str(self, origin):
        if not self.joins:
            return ""

        acc = []
        for join in self.joins:
            if join.many_table == self.frum:
                if len(join.many_columns) == 1:
                    acc.append(f".{join.many_columns[0]}")
                else:
                    acc.append(f".{value2json(join.many_columns)}")
                acc.append(join.many_table._more_str(origin))
            else:
                acc.append("->")
                acc.append(join.many_table._start_str(origin))
            acc.append(", ")

        if len(self.joins) == 1:
            return "".join(acc[:-1])
        else:
            return "[" + "".join(acc[:-1]) + "]"


@dataclass
class Join:
    ones_table: Source
    ones_columns: List[str]
    many_table: Source
    many_columns: List[str]

    def copy_and_replace(self, parent, old_origin, new_origin):
        if parent is self.ones_table:
            return Join(
                self.ones_table,
                self.ones_columns,
                self.many_table.copy_and_replace(old_origin, new_origin),
                self.many_columns,
            )
        else:
            return Join(
                self.ones_table.copy_and_replace(old_origin, new_origin),
                self.ones_columns,
                self.many_table,
                self.many_columns,
            )


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

    def copy_and_replace(self, old_origin, new_origin):
        return SqlLeftJoinsOp(self.frum.copy_and_replace(old_origin, new_origin), self.selects)

    @property
    def type(self):
        return JxType(**{s["name"]: s["value"] for s in self.selects})

    def __str__(self):
        return str(self.frum)
