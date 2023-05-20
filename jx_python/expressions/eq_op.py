# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import EqOp as EqOp_, is_literal, FALSE, TRUE, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_base.language import value_compare
from jx_python.expressions import Python
from jx_python.utils import merge_locals, to_python_list
from mo_json import JX_BOOLEAN, ARRAY_KEY


class EqOp(EqOp_):
    def to_python(self, loop_depth=0):
        lhs = ToArrayOp(self.lhs).partial_eval(Python).to_python(loop_depth)
        rhs = self.rhs.to_python(loop_depth)
        return PythonScript(
            merge_locals(rhs.locals, lhs.locals, ARRAY_KEY=ARRAY_KEY),
            loop_depth,
            JX_BOOLEAN,
            f"({rhs.source}) in ({to_python_list(lhs.source)})",
            self,
            FALSE,
        )

    def partial_eval(self, lang):
        lhs = self.lhs.partial_eval(lang)
        rhs = self.rhs.partial_eval(lang)

        if lhs is self.lhs and rhs is self.rhs:
            return self
        if is_literal(lhs) and is_literal(rhs):
            return FALSE if value_compare(lhs.value, rhs.value) else TRUE
        else:
            return EqOp(lhs, rhs)
