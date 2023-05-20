# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import exists

from jx_base.expressions import ExistsOp as ExistsOp_
from jx_base.expressions.python_script import PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_BOOLEAN


class ExistsOp(ExistsOp_):
    def to_python(self, loop_depth=0):
        expr = self.expr.to_python(loop_depth)
        return PythonScript(
            merge_locals(expr.locals, exists=exists), loop_depth, JX_BOOLEAN, f"exists({expr.source})", self
        )
