# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import LimitOp as LimitOp_, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python
from jx_python.utils import merge_locals, to_python_list
from mo_json import ARRAY_KEY


class LimitOp(LimitOp_):
    def to_python(self, loop_depth=0):
        frum = ToArrayOp(self.frum).partial_eval(Python).to_python(loop_depth)
        amount = self.amount.partial_eval(Python).to_python(loop_depth)
        return PythonScript(
            merge_locals(frum.locals, amount.locals, ARRAY_KEY=ARRAY_KEY),
            loop_depth,
            frum.type,
            f"{{ARRAY_KEY: ({to_python_list(frum.source)})[:{amount.source}]}}",
            self,
        )
