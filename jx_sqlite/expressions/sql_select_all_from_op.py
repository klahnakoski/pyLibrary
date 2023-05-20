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

from jx_base.expressions import (
    Variable,
    SqlSelectAllFromOp as _SqlSelectAllFrom,
    SqlSelectOp,
    AggregateOp,
)
from jx_base.expressions.sql_select_op import SqlAlias
from mo_dots import relative_field as mo_dots_relative_field
from jx_base.expressions.sql_left_joins_op import Source, Join
from jx_sqlite.expressions import SqlLeftJoinsOp
from jx_sqlite.expressions.sql_group_by_op import SqlGroupByOp
from jx_sqlite.expressions.sql_origins_op import SqlOriginsOp
from mo_json import to_jx_type, concat_field
from mo_sql.utils import untyped_column
from jx_sqlite.sqlite import ConcatSQL, SQL_SELECT, SQL_FROM, SQL_STAR, quote_column


class SqlSelectAllFromOp(_SqlSelectAllFrom):
    """
    REPRESENT ALL RECORDS IN A TABLE AS AN EXPRESSION
    SELECT * FROM table
    """

    @property
    def type(self):
        return self.table.schema.get_type()

    def query(self, expr):
        if isinstance(expr, Variable):
            # SIMPLE VARIABLE IN TABLE
            name = expr.var
            # ANY LEAVES WILL SHADOW TABLES
            cols = self.table.schema.get_columns(name)
            if cols:
                return SqlSelectOp(
                    self,
                    tuple(
                        SqlAlias(name, Variable(col.es_column, to_jx_type(col.json_type)))
                        for col in cols
                    ),
                )

            alt_origin = mo_dots_relative_field(self.table.name, self.table.schema.snowflake.fact_name)
            if alt_origin != ".":
                full_name, _ = untyped_column(concat_field(alt_origin, name))
                cols = self.table.schema.get_columns(full_name)
                if cols:
                    return SqlSelectOp(
                        self,
                        tuple(SqlAlias( name,Variable(col.es_column, to_jx_type(col.json_type)))
                            for col in cols
                        )
                    )

            relative_field, many_relations = self.table.schema.get_many_relations(name)
            if relative_field == ".":
                child_table = self.table.schema.get_table(many_relations.many_table)
                group = SqlSelectOp(
                    SqlSelectAllFromOp(child_table),
                    tuple(SqlAlias(c, Variable(c)) for c in many_relations.many_columns),
                )
                child_expr = SqlGroupByOp(SqlSelectAllFromOp(child_table), group)
                child = Source("t2", child_expr, [])
                parent = Source("t1", self, [])
                join = Join(
                    parent,
                    many_relations.ones_columns,
                    child,
                    many_relations.many_columns,
                )
                parent.joins.append(join)
                # CALC THE SELECTION (ASSUME SINGLE TABLE FIRST)
                return SqlOriginsOp(SqlLeftJoinsOp(parent, tuple()), child)
        elif isinstance(expr, AggregateOp):
            result = expr.frum.apply(self)
            return expr.op(result)

        raise NotImplementedError()

    def __str__(self):
        return str(self.to_sql(None))

    def to_sql(self, schema):
        return ConcatSQL(SQL_SELECT, SQL_STAR, SQL_FROM, quote_column(self.table.name))
