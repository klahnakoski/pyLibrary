# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import CountOp as CountOp_
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python
from mo_json import JX_INTEGER


class CountOp(CountOp_):
    def to_python(self, loop_depth=0):
        terms = self.terms.partial_eval(Python).to_python(loop_depth + 1)

        return PythonScript(
            terms.locals, loop_depth, JX_INTEGER, f"sum(((0 if v==None else 1) for v in {terms.source}), 0)", self
        )
