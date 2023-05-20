# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.basic_substring_op import BasicSubstringOp as _BasicSubstringOp
from jx_base.expressions.python_script import PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_TEXT


class BasicSubstringOp(_BasicSubstringOp):
    def to_python(self, loop_depth=0):
        value = self.value.to_python(loop_depth)
        start = self.start.to_python(loop_depth)
        end = self.end.to_python(loop_depth)
        return PythonScript(
            merge_locals(value.locals, start.locals, end.locals),
            loop_depth,
            JX_TEXT,
            f"({value})[int({self.start.to_python(loop_depth)}):int({self.end.to_python(loop_depth)})]",
            self,
        )
