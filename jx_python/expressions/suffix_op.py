# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import SuffixOp as SuffixOp_
from jx_base.expressions.python_script import PythonScript


class SuffixOp(SuffixOp_):
    def to_python(self, loop_depth=0):
        return PythonScript(
            {}, loop_depth, f"({self.expr.to_python(loop_depth)}).endswith({self.suffix.to_python(loop_depth)})",
        )
