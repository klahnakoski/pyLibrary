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

from jx_base.expressions import NULL, Variable as Variable_, SelectOp, FALSE
from jx_sqlite.expressions._utils import check, SqlScript
from jx_sqlite.sqlite import quote_column
from jx_sqlite.utils import GUID
from mo_dots import concat_field
from mo_json.types import to_jx_type, T_INTEGER


class Variable(Variable_):
    @check
    def to_sql(self, schema):
        var_name = self.var
        if var_name == GUID:
            output = SqlScript(
                data_type=T_INTEGER,
                expr=quote_column(GUID),
                frum=self,
                miss=FALSE,
                schema=schema,
            )
            return output
        cols = list(schema.leaves(var_name))
        select = []
        for rel_name, col in cols:
            select.append({
                "name": concat_field(var_name, rel_name),
                "value": Variable(col.es_column, to_jx_type(col.json_type)),
                "aggregate": NULL
            })

        if len(select) == 0:
            return NULL.to_sql(schema)
        elif len(select) == 1:
            rel_name0, col0 = cols[0]
            type0 = concat_field(col0.name, rel_name0) + to_jx_type(col0.json_type)
            output = SqlScript(
                data_type=type0,
                expr=quote_column(col0.es_column),
                frum=Variable(self.var, type0),
                schema=schema,
            )
            return output
        else:
            return SelectOp(schema, *select).to_sql(schema)
