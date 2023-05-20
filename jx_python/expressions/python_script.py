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

from jx_base.expressions import FALSE, TRUE, PythonScript as PythonScript_
from jx_python.expressions import Python


class PythonScript(PythonScript_):
    def __str__(self):
        missing = self.miss.partial_eval(Python)
        if missing is FALSE:
            return self.partial_eval(Python).to_python(self.loop_depth).source
        elif missing is TRUE:
            return "None"

        missing = missing.to_python(self.loop_depth)

        return f"None if {missing.source}) else ({self.source})"

    def __add__(self, other):
        return str(self) + str(other)

    def __radd__(self, other):
        try:
            a = str(other)
            b = str(self)
            return a + b
        except Exception as cause:
            b = str(self)
            return ""

    def to_python(self, loop_depth=0):
        return self

    def missing(self, lang):
        return self.miss

    def __data__(self):
        return {"script": self.script}

    def __eq__(self, other):
        if not isinstance(other, PythonScript_):
            return False
        elif self.expr == other.frum:
            return True
        else:
            return False
