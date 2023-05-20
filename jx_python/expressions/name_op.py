# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from jx_base.expressions import NameOp as NameOp_
from jx_base.expressions.python_script import PythonScript
from jx_python.expressions import Python
from mo_json import JxType


def add_name(value, name):
    return {name: value}


class NameOp(NameOp_):
    def to_python(self, loop_depth=0):
        frum = self.frum.partial_eval(Python).to_python(loop_depth)
        _name = self._name.partial_eval(Python).to_python(loop_depth)

        return PythonScript(
            {"add_name": add_name, **frum.locals, **_name.locals},
            loop_depth,
            JxType(**{self._name.value: frum.type}),  # assume literal name
            f"add_name({frum.source}, {_name.source})",
            self,
        )
