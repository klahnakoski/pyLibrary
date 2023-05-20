# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import CallOp as CallOp_, PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_ANY


class CallOp(CallOp_):
    def to_python(self, loop_depth=0):
        func = self.func.to_python(loop_depth)
        if self.args:
            arg_source, arg_locals = zip(*((c.source, c.locals) for a in self.args for c in [a.to_python(loop_depth)]))
        else:
            arg_source, arg_locals = tuple(), tuple()
        if self.kwargs:
            kwargs_keys, kwargs_source, kwargs_locals = zip(
                *((k, c.source, c.locals) for k, v in self.kwargs for c in [v.to_python(loop_depth)])
            )
        else:
            kwargs_keys, kwargs_source, kwargs_locals = tuple(), tuple(), tuple()
        args = ", ".join(arg_source + tuple(k + "=" + s for k, s in zip(kwargs_keys, kwargs_source)))

        return PythonScript(
            merge_locals(arg_locals, kwargs_locals, func.locals), loop_depth, JX_ANY, f"{func.source}({args})", self,
        )
