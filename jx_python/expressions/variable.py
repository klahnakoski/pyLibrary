# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_logs import logger

from jx_base.expressions import Variable as Variable_
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions.get_op import get_attr
from jx_python.utils import merge_locals
from mo_json import JX_ANY


class Variable(Variable_):
    def to_python(self, loop_depth=0):
        if self.var == ".":
            return PythonScript({}, loop_depth, JX_ANY, f"row{loop_depth}", self)
        if self.var not in ["row", "rownum", "rows"]:
            if loop_depth == 0:
                # WE ASSUME THIS IS NAIVE PYTHON EXPRESSION BUILD
                return PythonScript(
                    merge_locals(get_attr=get_attr), loop_depth, JX_ANY, f"get_attr(row{loop_depth}, {self.var})", self
                )

            logger.error("not expected")
        return PythonScript({}, loop_depth, JX_ANY, f"{self.var}{loop_depth}", self)
