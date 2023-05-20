# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from os.path import exists

from jx_base.expressions import ConcatOp as ConcatOp_
from jx_base.expressions.python_script import PythonScript
from jx_python.utils import merge_locals
from mo_json import JX_TEXT


class ConcatOp(ConcatOp_):
    def to_python(self, loop_depth=0):
        locals, sources = zip(*((c.locals, c.source) for t in self.terms for c in [t.to_python(loop_depth)]))
        separator = self.separator.to_python(loop_depth)
        csv = ",".join(sources)
        return PythonScript(
            merge_locals(locals, separator.locals, concat=concat),
            loop_depth,
            JX_TEXT,
            f"concat({separator}, *[{csv}])",
            self,
        )


def concat(separator, *values):
    if not values:
        return None
    if separator == None:
        separator = ""
    return separator.join(v for v in values if exists(v))
