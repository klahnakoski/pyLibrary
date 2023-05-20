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

from jx_base.expressions.python_script import PythonScript
from jx_base.expressions.to_number_op import ToNumberOp as NumberOp_
from jx_python.utils import merge_locals
from mo_json.types import JX_NUMBER


class ToNumberOp(NumberOp_):
    def to_python(self, loop_depth=0):
        exists = self.term.exists()
        value = self.term.to_python(loop_depth)

        return PythonScript(
            merge_locals(value.locals, to_float=to_float),
            loop_depth,
            JX_NUMBER,
            f"to_float({value.source})",
            self,
            exists,
        )


def to_float(value):
    try:
        return float(value)
    except:
        return None


export("jx_python.expressions._utils", ToNumberOp)
