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

from jx_base.expressions import ToBooleanOp as ToBooleanOp_, FALSE, TRUE, is_literal
from jx_sqlite.expressions._utils import SQLang, check
from mo_dots import Null
from mo_json.types import T_BOOLEAN, base_type


class ToBooleanOp(ToBooleanOp_):
    @check
    def to_sql(self, schema):
        term = self.term.partial_eval(SQLang)
        if base_type(term.type) == T_BOOLEAN:
            return term.to_sql(schema)
        elif is_literal(term):
            try:
                return _map[term.value]
            except:
                pass

        return term.exists().partial_eval(SQLang).to_sql(schema)


_map = {"T": TRUE.to_sql(Null), "F": FALSE.to_sql(Null)}
