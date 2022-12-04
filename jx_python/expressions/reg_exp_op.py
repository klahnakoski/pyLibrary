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

from mo_logs.strings import quote

from jx_base.expressions import RegExpOp as RegExpOp_


class RegExpOp(RegExpOp_):
    def to_python(self):
        return (
            "re.match("
            + quote(self.pattern.value + "$")
            + ", "
            + self.expr.to_python()
            + ")"
        )
