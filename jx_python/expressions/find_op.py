# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions import FindOp as FindOp_
from jx_python.expressions._utils import with_var, Python, PythonScript
from jx_python.expressions.and_op import AndOp
from jx_python.expressions.basic_eq_op import BasicEqOp
from jx_python.expressions.basic_index_of_op import BasicIndexOfOp
from jx_python.expressions.eq_op import EqOp
from jx_python.expressions.literal import Literal
from jx_python.expressions.or_op import OrOp
from jx_python.expressions.when_op import WhenOp
from jx_python.utils import merge_locals
from mo_json import JX_INTEGER


class FindOp(FindOp_):
    def partial_eval(self, lang):
        index = BasicIndexOfOp(self.value, self.find, self.start).partial_eval(lang)

        output = WhenOp(
            OrOp(self.value.missing(Python), self.find.missing(Python), BasicEqOp(index, Literal(-1)),),
            then=self.default,
            **{"else": index},
        ).partial_eval(lang)
        return output

    def missing(self, lang):
        output = AndOp(
            self.default.missing(Python),
            OrOp(
                self.value.missing(Python),
                self.find.missing(Python),
                EqOp(BasicIndexOfOp(self.value, self.find, self.start), Literal(-1)),
            ),
        ).partial_eval(lang)
        return output

    def to_python(self, loop_depth=0):
        value = self.value.to_python(loop_depth)
        find = self.find.to_python(loop_depth)
        return PythonScript(
            merge_locals(value.locals, find.locals),
            loop_depth,
            JX_INTEGER,
            with_var("f", f"({value.source}).find({find.source})", "None if f==-1 else f",),
            self,
        )
