# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.basic_starts_with_op import BasicStartsWithOp as _BasicStartsWithOp
from jx_base.expressions.python_script import PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_BOOLEAN


class BasicStartsWithOp(_BasicStartsWithOp):
    def to_python(self, loop_depth=0):
        value = self.value.to_python(loop_depth)
        prefix = self.prefix.to_python(loop_depth)
        return PythonScript(
            merge_locals(value.locals, prefix.locals),
            loop_depth,
            JX_BOOLEAN,
            f"({value.source}).startswith({prefix.source})",
            self,
        )
