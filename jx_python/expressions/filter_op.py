# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import FilterOp as FilterOp_, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_base.utils import enlist
from jx_python.expressions import Python
from jx_python.utils import merge_locals, to_python_list
from mo_json import ARRAY_KEY


class FilterOp(FilterOp_):
    def to_python(self, loop_depth=0):
        frum = ToArrayOp(self.frum).partial_eval(Python).to_python(loop_depth)
        loop_depth = frum.loop_depth + 1
        predicate = self.predicate.partial_eval(Python).to_python(loop_depth)

        return PythonScript(
            merge_locals(frum.locals, predicate.locals, enlist=enlist, ARRAY_KEY=ARRAY_KEY),
            loop_depth,
            frum.type,
            f"""{{ARRAY_KEY: [row{loop_depth} for rows{loop_depth} in [{to_python_list(frum.source)}] for rownum{loop_depth}, row{loop_depth} in enumerate(rows{loop_depth}) if ({predicate.source})]}}""",
            self,
        )
