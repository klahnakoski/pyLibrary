# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import NotOp as NotOp_, PythonScript, ToBooleanOp, FALSE
from jx_python.expressions import Python
from mo_json import JX_BOOLEAN


class NotOp(NotOp_):
    def to_python(self, loop_depth=0):
        term = ToBooleanOp(self.term).partial_eval(Python).to_python(loop_depth)
        return PythonScript(term.locals, loop_depth, JX_BOOLEAN, "not (" + term.source + ")", self, FALSE)
