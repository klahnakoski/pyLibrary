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
from typing import Dict, Tuple, Optional

from jx_base.expressions import NULL
from jx_sqlite.expressions._utils import SQLang

from jx_base.expressions.expression import Expression
from jx_base.expressions.sql_select_op import SqlSelectOp as _SqlSelectOp
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import (
    ConcatSQL,
    SQL_FROM,
    SQL_SELECT,
    sql_alias,
    sql_list,
)
from mo_json import JxType, T_INTEGER


class SqlSelectOp(_SqlSelectOp):
    def __init__(self, frum, selects: Tuple[Dict[str, Expression]]):
        _SqlSelectOp.__init__(self, frum, selects)

    def apply(self, container):
        print("details")

    def to_sql(self, schema):
        return SqlScript(
            data_type=self.type,
            expr=ConcatSQL(
                SQL_SELECT,
                sql_list(
                    *(
                        sql_alias(v.to_sql(schema), n)
                        for n, v in self.selects.items()
                    )
                ),
                SQL_FROM,
                self.frum.to_sql(schema),
            ),
            frum=self,
            miss=self.frum.missing(SQLang),
            schema=schema,
        )

    @property
    def type(self):
        return JxType(
            **{
                s['name']: s['value'].type
                for s in self.selects
            }
        )


@dataclass
class About:
    func_name: str
    zero: float
    type: Optional[JxType]


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
