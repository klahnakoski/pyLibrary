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

from jx_base.expressions import SelectOp as SelectOp_, LeavesOp, Variable, AndOp, NULL
from jx_base.language import is_op
from jx_sqlite.expressions._utils import check, SQLang
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import (
    quote_column,
    SQL_COMMA,
    SQL_AS,
    SQL_SELECT,
    SQL,
    Log,
    ENABLE_TYPE_CHECKING, SQL_CR,
)
from mo_dots import concat_field, literal_field
from mo_json.types import to_jx_type, T_IS_NULL


class SelectOp(SelectOp_):
    @check
    def to_sql(self, schema):
        type = T_IS_NULL
        sql_terms = []
        diff = False
        for name, expr in self:
            if is_op(expr, Variable):
                var_name = expr.var
                cols = list(schema.leaves(var_name))
                if len(cols) == 0:
                    sql_terms.append({
                        "name": name,
                        "value": NULL
                    })
                    continue
                elif len(cols) == 1:
                    rel_name0, col0 = cols[0]
                    if col0.es_column == var_name:
                        # WHEN WE REQUEST AN ES_COLUMN DIRECTLY, BREAK THE RECURSIVE LOOP
                        full_name = concat_field(name, rel_name0)
                        type |= full_name + to_jx_type(col0.json_type)
                        sql_terms.append({
                            "name": full_name,
                            "value": expr
                        })
                        continue

                diff = True
                for rel_name, col in cols:
                    full_name = concat_field(name, rel_name)
                    type |= full_name + to_jx_type(col.json_type)
                    sql_terms.append({
                        "name": full_name,
                        "value": Variable(col.es_column, col.json_type),
                    })
            elif is_op(expr, LeavesOp):
                var_names = expr.term.vars()
                for var_name in var_names:
                    cols = schema.leaves(var_name)
                    diff = True
                    for rel_name, col in cols:
                        full_name = concat_field(name,  literal_field(rel_name))
                        type |= full_name + to_jx_type(col.json_type)
                        sql_terms.append({
                            "name": full_name,
                            "value": Variable(col.es_column, col.json_type),
                        })
            else:
                type |= name + to_jx_type(expr.type)
                sql_terms.append({
                    "name": name,
                    "value": expr,
                })

        if diff:
            return SelectOp(schema, *sql_terms).partial_eval(SQLang).to_sql(schema)

        return SqlScript(
            data_type=type,
            expr=SelectSQL(sql_terms, schema),
            miss=AndOp(*tuple(t["value"].missing(SQLang) for t in sql_terms)),
            frum=self,
            schema=schema,
        )


class SelectSQL(SQL):
    __slots__ = ["terms", "schema"]

    def __init__(self, terms, schema):
        if ENABLE_TYPE_CHECKING:
            if not isinstance(terms, list) or not all(isinstance(term, dict) for term in terms):
                Log.error("expecting list of dicts")
        self.terms = terms
        self.schema = schema

    def __iter__(self):
        for s in SQL_SELECT:
            yield s
        comma = SQL_CR
        for term in self.terms:
            name, value = term["name"], term["value"]
            for s in comma:
                yield s
            comma = SQL_COMMA
            for s in value.to_sql(self.schema):
                yield s
            for s in SQL_AS:
                yield s
            for s in quote_column(name):
                yield s
