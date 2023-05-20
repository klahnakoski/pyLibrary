# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from mo_times.dates import Date

from jx_base.expressions import DateOp as DateOp_
from jx_base.expressions.python_script import PythonScript


class DateOp(DateOp_):
    def to_python(self, loop_depth=0):
        return PythonScript({}, loop_depth, str(Date(self.value).unix))
