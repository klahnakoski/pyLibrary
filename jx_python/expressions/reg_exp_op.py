# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import re

from jx_base.expressions import RegExpOp as RegExpOp_
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python
from jx_python.utils import merge_locals
from mo_json import JX_BOOLEAN


class RegExpOp(RegExpOp_):
    def to_python(self, loop_depth=0):
        pattern = self.pattern.partial_eval(Python).to_python(loop_depth)
        expr = self.expr.partial_eval(Python).to_python(loop_depth)
        return PythonScript(
            merge_locals(pattern.locals, expr.locals, re=re),
            loop_depth,
            JX_BOOLEAN,
            f"re.match({pattern.source}, {expr.source})",
            self,
        )
