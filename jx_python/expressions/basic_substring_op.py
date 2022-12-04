# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import absolute_import, division, unicode_literals

from jx_base.expressions.basic_substring_op import BasicSubstringOp as _BasicSubstringOp


class BasicSubstringOp(_BasicSubstringOp):
    def to_python(self):
        value = self.value.to_python()
        return f"({value})[int({self.start.to_python()}):int({self.end.to_python()})]"
