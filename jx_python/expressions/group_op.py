# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import itertools

from mo_dots import is_data
from mo_future import sort_using_cmp

from jx_base.expressions import GroupOp as GroupOp_, ToArrayOp
from jx_base.expressions.python_script import PythonScript
from jx_base.language import value_compare
from jx_python.expressions import Python
from jx_python.utils import merge_locals, to_python_list
from mo_json.typed_encoder import detype
from mo_json.typed_object import entype, entype_array, TypedObject
from mo_json.types import JxType, array_of, ARRAY_KEY

ARRAY_KEY = ARRAY_KEY


class GroupOp(GroupOp_):
    def to_python(self, loop_depth=0):
        frum = ToArrayOp(self.frum).partial_eval(Python).to_python(loop_depth)
        group = self.group.partial_eval(Python).to_python(loop_depth)

        return PythonScript(
            merge_locals(frum.locals, group.locals, groupby=groupby, detype=detype, entype=entype),
            loop_depth,
            array_of(frum.type) | JxType(group=group.type),
            f"""{{ARRAY_KEY: groupby({frum.source}, lambda row{loop_depth}: {group.source})}}""",
            self,
        )


def groupby(values, func):
    output = []
    cmp = lambda a, b: value_compare(detype(func(a)), detype(func(b)))
    for g, rows in itertools.groupby(sort_using_cmp(values[ARRAY_KEY], cmp=cmp), func):
        row = TypedObject([detype(v) for v in rows])
        if is_data(g):
            output.append({ARRAY_KEY: row, **g})
        else:
            output.append({ARRAY_KEY: row})
    return output
