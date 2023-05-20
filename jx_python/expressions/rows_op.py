# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from mo_dots import split_field

from jx_base.expressions.python_script import PythonScript
from mo_json import json2value
from mo_logs import strings

from jx_base.expressions import RowsOp as RowsOp_
from jx_python.expressions.to_integer_op import ToIntegerOp


class RowsOp(RowsOp_):
    def to_python(self, loop_depth=0):
        agg = "rows[rownum+" + (ToIntegerOp(self.offset)).to_python(loop_depth) + "]"
        path = split_field(json2value(self.var.json))
        if not path:
            return PythonScript({}, loop_depth, agg)

        for p in path[:-1]:
            agg = agg + ".get(" + strings.quote(p) + ", EMPTY_DICT)"
        return PythonScript({"EMPTY_DICT": {}}, loop_depth, agg + ".get(" + strings.quote(path[-1]) + ")",)
