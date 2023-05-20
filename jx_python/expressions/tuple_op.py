# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import TupleOp as TupleOp_
from jx_base.expressions.python_script import PythonScript


class TupleOp(TupleOp_):
    def to_python(self, loop_depth=0):
        if len(self.terms) == 0:
            return PythonScript({}, loop_depth, "tuple()")
        elif len(self.terms) == 1:
            return PythonScript({}, loop_depth, "(" + (self.terms[0]).to_python(loop_depth) + ",)")
        else:
            return PythonScript({}, loop_depth, "(" + ",".join((t).to_python(loop_depth) for t in self.terms) + ")",)
