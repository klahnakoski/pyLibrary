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

from jx_base.expressions.expression import Expression
from jx_base.expressions.null_op import NULL
from mo_json.types import JxType, JX_INTEGER


class SqlGroupByOp(Expression):
    def __init__(self, frum, group):
        Expression.__init__(self, frum, group)
        self.frum = frum
        self.group = group


@dataclass
class About:
    func_name: str
    zero: float
    type: JxType


_count = About("COUNT", 0, JX_INTEGER)
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
