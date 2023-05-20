# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import GetOp as GetOp_, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_base.utils import enlist
from jx_python.expressions import Python
from jx_python.utils import merge_locals, to_python_list
from mo_json import JX_ANY, array_of, ARRAY_KEY


class GetOp(GetOp_):
    def to_python(self, loop_depth=0):
        offsets, locals = zip(*((c.source, c.locals) for o in self.offsets for c in [o.to_python(loop_depth)]))
        offsets = ", ".join(offsets)
        frum = ToArrayOp(self.frum).partial_eval(Python).to_python(loop_depth)
        # TODO: should be able to reach into frum.type to get actual type
        var_type = array_of(JX_ANY)

        return PythonScript(
            merge_locals(locals, frum.locals, get_attr=get_attr, ARRAY_KEY=ARRAY_KEY),
            loop_depth,
            var_type,
            f"{{ARRAY_KEY: get_attr({to_python_list(frum.source)}, {offsets})}}",
            self,
        )


def unit(x):
    return x


def get_attr(values, *items):
    for item in items:
        result = []
        for v in values:
            try:
                child = getattr(v, item)
            except:
                try:
                    child = v[item]
                except:
                    continue

            if isinstance(child, dict) and ARRAY_KEY in child:
                result.extend(child[ARRAY_KEY])
            else:
                result.extend(enlist(child))

        values = result
    return values
