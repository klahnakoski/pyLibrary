# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import NeOp as NeOp_
from jx_python.expressions._utils import with_var, PythonSource


class NeOp(NeOp_):
    def to_python(self, loop_depth=0):
        lhs = self.lhs.to_python(loop_depth)
        rhs = self.rhs.to_python(loop_depth)

        return PythonScript(
            {**lhs.locals, **rhs.locals},
            loop_depth,
            with_var("r, l", "(" + lhs + "," + rhs + ")", "l!=None and r!=None and l!=r"),
        )
