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
from jx_base.expressions.sql_left_joins_op import Source, Join
from jx_sqlite.expressions import SqlLeftJoinsOp
from mo_json import to_jx_type


class SqlSelectAllFromOp(_SqlSelectAllFrom):
    """
    REPRESENT ALL RECORDS IN A TABLE AS AN EXPRESSION
    SELECT * FROM table
    """

    def __init__(self, table, group_by):
        _SqlSelectAllFrom.__init__(self, table)
        self.group_by = group_by

    @property
    def type(self):
        return self.table.schema.get_type()

    def query(self, expr, group_by):
        if isinstance(expr, Variable):
            # SIMPLE VARIABLE IN TABLE
            name = expr.var

            # ANY LEAVES WILL SHADOW TABLES
            cols = self.table.schema.get_columns(name)
            if cols:
                return SqlSelectOp(
                    self,
                    tuple(
                        {
                            "name": col.es_column,
                            "value": Variable(col.es_column, to_jx_type(col.json_type)),
                        }
                        for col in cols
                    )
                )

            relative_field, many_relations = self.table.schema.get_many_relations(name)
            if relative_field == ".":
                # ATTACH SNOWFLAKE
                # FIND SPANNING TREE
                # RETURN WHOLE QUERY? - NO, RETURN OPEN QUERY FOR LAZY EVALUATION
                many_group_by = tuple(
                    m
                    for c in self.group_by
                    for m, o in zip(
                        many_relations.many_columns, many_relations.ones_columns
                    )
                    if c == o
                )
                child_table = self.table.schema.get_table(many_relations.many_table)
                child_expr = SqlSelectAllFromOp(
                    child_table,
                    many_group_by,
                ).query(Variable("."), many_group_by+child_table.schema.get_primary_keys())
                child = Source("t1", child_expr, [])
                parent = Source("t2", self, [])
                join = Join(
                    parent,
                    many_relations.ones_columns,
                    child,
                    many_relations.many_columns,
                )
                parent.joins.append(join)

                """
                SELECT 
                    t1.__id__,
                    t2.__id__,
                    t2.__parent__,
                    t2.__order__,
                    t2.`a._b.a.$n`,
                    t2.`a._b.b.$n`,
                FROM
                    testing t1
                LEFT JOIN (
                    SELECT
                        __id__,
                        __parent__,
                        __order__,
                        `a._b.a.$n`,
                        `a._b.b.$n`,
                    FROM                                           
                        `testing.a._b.$a`
                    GROUP BY
                        __parent__,
                        __id__
                    ) t2 ON t2.__parent__ = t1.__id__
                GROUP BY
                    t1.__id__
                """

                # CALC THE SELECTION (ASSUME SINGLE TABLE FIRST)
                return SqlLeftJoinsOp(parent, tuple())
        elif isinstance(expr, AggregateOp):
            result = expr.frum.apply(self)
            return expr.op(result)

        raise NotImplementedError()
