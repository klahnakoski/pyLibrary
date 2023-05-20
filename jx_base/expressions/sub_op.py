# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.base_binary_op import BaseBinaryOp


class SubOp(BaseBinaryOp):
    op = "sub"

    def __call__(self, row=None, rownum=None, rows=None):
        lhs = self.lhs(row)
        rhs = self.rhs(row)
        if not isinstance(lhs, (float, int)) or not isinstance(rhs, (float, int)):
            return None
        return lhs - rhs
