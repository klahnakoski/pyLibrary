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

from jx_base.expressions import RightOp as RightOp_, ZERO
from jx_base.expressions._utils import simplified
from jx_sqlite.expressions import SQLang
from jx_sqlite.expressions.basic_substring_op import BasicSubstringOp
from jx_sqlite.expressions.length_op import LengthOp
from jx_sqlite.expressions.max_op import MaxOp
from jx_sqlite.expressions.min_op import MinOp
from jx_sqlite.expressions.sub_op import SubOp


class RightOp(RightOp_):
    @simplified
    def partial_eval(self, lang):
        value = self.value.partial_eval(SQLang)
        length = self.length.partial_eval(SQLang)
        max_length = LengthOp(value)

        return BasicSubstringOp([
            value,
            MaxOp([ZERO, MinOp([max_length, SubOp([max_length, length])])]),
            max_length,
        ])
