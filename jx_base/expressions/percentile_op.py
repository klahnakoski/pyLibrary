# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.base_multi_op import BaseMultiOp


class PercentileOp(BaseMultiOp):
    op = "percentile"

    def __init__(self, *terms, default=None, nulls=False, **clauses):
        BaseMultiOp.__init__(terms, default, nulls, **clauses)
        self.percentile = 0.50
