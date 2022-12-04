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

from mo_json.types import T_NUMBER_TYPES

from jx_base.expressions.to_number_op import ToNumberOp as NumberOp_
from jx_base.expressions.true_op import TRUE
from jx_python.expressions import _utils


class ToNumberOp(NumberOp_):
    def to_python(self):
        term = self.term
        exists = self.term.exists()
        value = self.term.to_python()

        if exists is TRUE:
            if term.type in T_NUMBER_TYPES:
                return value
            return "float(" + value + ")"
        else:
            return (
                "float(" + value + ") if (" + exists.to_python() + ") else None"
            )


_utils.ToNumberOp = ToNumberOp
