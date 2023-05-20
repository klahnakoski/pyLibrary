# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import ToArrayOp as _ToArrayOp, PythonScript
from jx_base.utils import enlist
from jx_python.expressions import Python
from jx_python.streams import entype
from jx_python.utils import merge_locals
from mo_json import array_of, ARRAY
from mo_json.typed_encoder import detype
from mo_json.types import ARRAY_KEY


class ToArrayOp(_ToArrayOp):
    def to_python(self, loop_depth=0):
        term = self.term.partial_eval(Python).to_python(loop_depth)
        type = term.type
        if type == ARRAY:
            return PythonScript(merge_locals(term.locals, enlist=enlist, entype=entype, detype=detype), loop_depth, type, term.source, self)

        return PythonScript(
            merge_locals(term.locals, enlist=enlist, entype=entype, detype=detype, ARRAY_KEY=ARRAY_KEY),
            loop_depth,
            array_of(term.type),
            f"entype(enlist(detype({term.source})))",
            self,
        )
