# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_future import extend

from jx_base.expressions import FalseOp as FalseOp_, FALSE
from jx_base.expressions.python_script import PythonScript
from mo_json import JX_BOOLEAN


class FalseOp(FalseOp_):
    def to_python(self, loop_depth=0):
        return PythonScript({}, loop_depth, JX_BOOLEAN, "False", self, FALSE)


extend(FalseOp_)(FalseOp.to_python)
