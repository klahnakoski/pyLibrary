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

from mo_dots import exists

from jx_base.expressions.base_multi_op import BaseMultiOp


class AddOp(BaseMultiOp):
    op = "add"

    def __call__(self, row=None, rownum=None, rows=None):
        return sum(v for t in self.terms for v in [t(row, rownum, rows)] if exists(v))