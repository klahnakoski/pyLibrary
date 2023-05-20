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

from jx_base.expressions import OrOp as OrOp_, FALSE, PythonScript, ToBooleanOp
from jx_python.utils import merge_locals
from mo_json import JX_BOOLEAN


class OrOp(OrOp_):
    def to_python(self, loop_depth=0):
        locals, sources = zip(
            *((p.locals, p.source) for t in self.terms for p in [ToBooleanOp(t).to_python(loop_depth)])
        )
        return PythonScript(
            merge_locals(*locals),
            loop_depth,
            JX_BOOLEAN,
            " or ".join(f"({source})" for source in sources),
            self,
            FALSE,
        )


export("jx_python.expressions._utils", OrOp)
