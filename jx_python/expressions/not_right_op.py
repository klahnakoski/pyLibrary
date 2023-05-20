# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import NotRightOp as NotRightOp_
from jx_base.expressions.python_script import PythonScript


class NotRightOp(NotRightOp_):
    def to_python(self, loop_depth=0):
        v = self.value.to_python(loop_depth)
        l = self.length.to_python(loop_depth)
        return PythonScript(
            {**v.locals, **l.locals},
            loop_depth,
            (
                "None if "
                + v.source
                + " == None or "
                + l.source
                + " == None else "
                + v.source
                + "[0:max(0, len("
                + v.source
                + ")-("
                + l.source
                + "))]"
            ),
        )
