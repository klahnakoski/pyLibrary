# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import LastOp as LastOp_, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python
from jx_python.utils import merge_locals, to_python_list
from mo_json import member_type, ARRAY_KEY


class LastOp(LastOp_):
    def to_python(self, loop_depth=0):
        term = ToArrayOp(self.term).partial_eval(Python).to_python(loop_depth)
        return PythonScript(
            merge_locals(term.locals, last=last, ARRAY_KEY=ARRAY_KEY),
            loop_depth,
            member_type(term.type),
            f"last({to_python_list(term.source)})",
            self,
        )


def last(values):
    if not last:
        return None
    return values[-1]
