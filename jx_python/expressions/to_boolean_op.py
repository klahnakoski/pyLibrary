# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import ToBooleanOp as ToBooleanOp_, FALSE, PythonScript
from jx_python.expressions._utils import with_var
from mo_json import JX_BOOLEAN


class ToBooleanOp(ToBooleanOp_):
    def to_python(self, loop_depth=0):
        term = self.term.to_python(loop_depth)
        if term.type == JX_BOOLEAN:
            return term
        return PythonScript(term.locals, loop_depth, JX_BOOLEAN, with_var("f", term.source, "bool(f)"), self, FALSE)
