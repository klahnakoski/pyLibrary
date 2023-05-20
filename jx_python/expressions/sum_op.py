# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import exists

from jx_base.expressions import SumOp as SumOp_, PythonScript, ToArrayOp
from jx_python.expressions import Python
from jx_python.utils import merge_locals, to_python_list
from mo_json import JX_NUMBER


class SumOp(SumOp_):
    def to_python(self, loop_depth=0):
        terms = ToArrayOp(self.terms).partial_eval(Python).to_python(loop_depth)
        loop_depth = terms.loop_depth + 1
        source = f"""sum(row{loop_depth} for row{loop_depth} in {to_python_list(terms.source)} if exists(row{loop_depth})"""
        return PythonScript(
            merge_locals(terms.locals, exists=exists), loop_depth, JX_NUMBER, source, self)
