# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import AvgOp as AvgOp_
from jx_python.expressions._utils import multiop_to_python, with_var, PythonSource


class AvgOp(AvgOp_):
    to_python = multiop_to_python

    def to_python(self, loop_depth=0):
        default = self.default.to_python(loop_depth)
        return PythonScript(
            {}, loop_depth, with_var("x", self.terms.to_python(loop_depth), f"sum(x)/count(x) if x else {default}",),
        )
