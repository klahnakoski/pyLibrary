# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_imports import export

from jx_base.expressions import ScriptOp as ScriptOp_
from jx_base.expressions.python_script import PythonScript


class ScriptOp(ScriptOp_):
    def to_python(self, loop_depth=0):
        return PythonScript({}, loop_depth, self.script)


export("jx_python.expressions._utils", ScriptOp)
