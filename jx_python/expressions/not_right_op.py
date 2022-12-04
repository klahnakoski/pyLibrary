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

from jx_base.expressions import NotRightOp as NotRightOp_


class NotRightOp(NotRightOp_):
    def to_python(self):
        v = (self.value).to_python()
        l = (self.length).to_python()
        return (
            "None if "
            + v
            + " == None or "
            + l
            + " == None else "
            + v
            + "[0:max(0, len("
            + v
            + ")-("
            + l
            + "))]"
        )
