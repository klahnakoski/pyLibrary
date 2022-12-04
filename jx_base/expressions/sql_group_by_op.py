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

from dataclasses import dataclass

from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_sqlite.sqlite import (
    sql_call,
    ConcatSQL,
    SQL_FROM,
    SQL_GROUPBY,
    SQL_SELECT,
    sql_alias,
    sql_list,
)
from mo_dots import coalesce


class SqlGroupByOp(Expression):
    def __init__(self, frum, groups, selects, ops):
        if TYPE_CHECK:
            if not isinstance(groups, list):
                Log.error("expecting groups to be a list of expressions")
            if (
                not isinstance(selects, tuple)
                and not all(isinstance(s, dict) for s in selects[1:])
                or any(s.get("name") is None for s in selects)
            ):
                Log.error("expecting list of dicts with 'name' and 'value' property")
            if not isinstance(ops, list) and all(o in sql_aggregates for o in ops):
                Log.error("expecting ops to be a list of aggregates ")
        Expression.__init__(self, frum, groups, selects)
        self.frum = frum
        self.group = group
        self.selects = selects
        self.op = op

    def to_sql(self, schema):
        groups = [
            sql_alias(g.to_sql(schema), f"g{i}") for i, g in enumerate(self.groups)
        ]
        selects = [
            sql_alias(sql_call(sql_aggregates[o].func_name, s.to_sql(schema)), s['name'])
            for i, s in eunmerate(zip(self.ops, self.selects))
        ]

        return SqlScript(
            data_type=self.type,
            expr=ConcatSQL(
                SQL_SELECT,
                sql_list(*groups, *selects),
                SQL_FROM,
                self.frum.to_sql(schema),
                SQL_GROUPBY,
                sql_list(*groups),
            ),
            frum=self,
            miss=FALSE,
            schema=schema,
        )

    @property
    def type(self):
        return JxType(
            **{f"g{i}": g.type for i, g in enumerate(self.groups)},
            **{
                f"c{i}": coalesce(sql_aggregates[o].type, s.type)
                for i, s in eunmerate(zip(self.ops, self.selects))
            },
        )


@dataclass
class About:
    func_name: str
    zero: float
    type: JxType


_count = About("COUNT", 0, T_INTEGER)
_min = About("MIN", NULL, None)
_max = About("MAX", NULL, None)
_sum = About("SUM", NULL, None)
_avg = About("AVG", NULL, None)


sql_aggregates = {
    "count": _count,
    "min": _min,
    "minimum": _min,
    "max": _max,
    "maximum": _max,
    "add": _sum,
    "sum": _sum,
    "avg": _avg,
    "average": _avg,
    "mean": _avg,
}
