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

from mo_imports import export

import mo_json
from jx_base import Column, Facts
from jx_base.expressions import jx_expression, QueryOp, SelectOp, Variable, FromOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.select_op import normalize_one
from jx_base.models.container import type2container
from jx_sqlite.expressions._utils import SQLang
from jx_sqlite.groupby_table import GroupbyTable
from jx_sqlite.sqlite import (
    SQL_FROM,
    SQL_ORDERBY,
    SQL_SELECT,
    SQL_WHERE,
    sql_count,
    sql_iso,
    sql_list,
    SQL_DELETE,
    ConcatSQL,
    JoinSQL,
    SQL_COMMA,
)
from jx_sqlite.sqlite import quote_column, sql_alias
from jx_sqlite.utils import GUID, sql_aggs, untyped_column
from mo_dots import (
    Data,
    coalesce,
    concat_field,
    relative_field,
    unwraplist,
    list_to_data)
from mo_future import text
from mo_json import STRING, STRUCT, to_jx_type
from mo_logs import Log
from mo_threads import register_thread


class QueryTable(GroupbyTable):
    def __init__(self, name, container):
        Facts.__init__(self, name, container)

    def get_column_name(self, column):
        return relative_field(column.name, self.snowflake.fact_name)

    @register_thread
    def __len__(self):
        counter = self.container.db.query(ConcatSQL(
            SQL_SELECT, sql_count("*"), SQL_FROM, quote_column(self.snowflake.fact_name)
        ))[0][0]
        return counter

    def __nonzero__(self):
        return bool(self.__len__())

    def delete(self, where):
        filter = jx_expression(where).partial_eval(SQLang).to_sql(self.schema)
        with self.container.db.transaction() as t:
            t.execute(ConcatSQL(
                SQL_DELETE,
                SQL_FROM,
                quote_column(self.snowflake.fact_name),
                SQL_WHERE,
                filter,
            ))

    def vars(self):
        return set(self.schema.columns.keys())

    def map(self, map_):
        return self

    def where(self, filter):
        """
        WILL NOT PULL WHOLE OBJECT, JUST TOP-LEVEL PROPERTIES
        :param filter:  jx_expression filter
        :return: list of objects that match
        """
        select = []
        column_names = []
        for c in self.schema.columns:
            if c.json_type in STRUCT:
                continue
            if len(c.nested_path) != 1:
                continue
            column_names.append(c.name)
            select.append(sql_alias(quote_column(c.es_column), c.name))

        where_sql = jx_expression(filter).partial_eval(SQLang).to_sql(self.schema)
        result = self.container.db.query(ConcatSQL(
            SQL_SELECT,
            JoinSQL(SQL_COMMA, select),
            SQL_FROM,
            quote_column(self.snowflake.fact_name),
            SQL_WHERE,
            where_sql,
        ))

        return list_to_data([
            {c: v for c, v in zip(column_names, r)} for r in result.data
        ])

    def query(self, query: Expression, group_by):
        if isinstance(query, Variable):
            column = self.schema.column(query.var)
            return SelectOp(self, *[{"name": query.var, "value": Variable(c.es_column, to_jx_type(c.json_type))} for c in column])
        elif isinstance(query, FromOp):
            pass # TODO: select sub table
        Log.error("do not know yet")

    def query_metadata(self, query):
        frum, query["from"] = query["from"], self
        schema = self.snowflake.tables["."].schema
        query = QueryOp.wrap(query, schema)
        columns = self.snowflake.columns
        where = query.where
        table_name = None
        column_name = None

        if query.edges or query.groupby:
            raise Log.error("Aggregates(groupby or edge) are not supported")

        if where.op == "eq" and where.lhs.var == "table":
            table_name = mo_json.json2value(where.rhs.json)
        elif where.op == "eq" and where.lhs.var == "name":
            column_name = mo_json.json2value(where.rhs.json)
        else:
            raise Log.error(
                'Only simple filters are expected like: "eq" on table and column name'
            )

        tables = [concat_field(self.snowflake.fact_name, i) for i in self.tables.keys()]

        metadata = []
        if columns[-1].es_column != GUID:
            columns.append(Column(
                name=GUID,
                json_type=STRING,
                es_column=GUID,
                es_index=self.snowflake.fact_name,
                nested_path=["."],
            ))

        for tname, table in zip(t, tables):
            if table_name != None and table_name != table:
                continue

            for col in columns:
                cname, ctype = untyped_column(col.es_column)
                if column_name != None and column_name != cname:
                    continue

                metadata.append((
                    table,
                    relative_field(col.name, tname),
                    col.type,
                    unwraplist(col.nested_path),
                ))

        if query.format == "cube":
            num_rows = len(metadata)
            header = ["table", "name", "type", "nested_path"]
            temp_data = dict(zip(header, zip(*metadata)))
            return Data(
                meta={"format": "cube"},
                data=temp_data,
                edges=[{
                    "name": "rownum",
                    "domain": {
                        "type": "rownum",
                        "min": 0,
                        "max": num_rows,
                        "interval": 1,
                    },
                }],
            )
        elif query.format == "table":
            header = ["table", "name", "type", "nested_path"]
            return Data(meta={"format": "table"}, header=header, data=metadata)
        else:
            header = ["table", "name", "type", "nested_path"]
            return Data(
                meta={"format": "list"}, data=[dict(zip(header, r)) for r in metadata]
            )

    def _window_op(self, query, window):
        # http://www2.sqlite.org/cvstrac/wiki?p=UnsupportedSqlAnalyticalFunctions
        if window.value == "rownum":
            return (
                "ROW_NUMBER()-1 OVER ("
                + " PARTITION BY "
                + sql_iso(sql_list(window.edges.values))
                + SQL_ORDERBY
                + sql_iso(sql_list(window.edges.sort))
                + ") AS "
                + quote_column(window.name)
            )

        range_min = text(coalesce(window.range.min, "UNBOUNDED"))
        range_max = text(coalesce(window.range.max, "UNBOUNDED"))

        return (
            sql_aggs[window.aggregate]
            + sql_iso(window.value.to_sql(schema))
            + " OVER ("
            + " PARTITION BY "
            + sql_iso(sql_list(window.edges.values))
            + SQL_ORDERBY
            + sql_iso(sql_list(window.edges.sort))
            + " ROWS BETWEEN "
            + range_min
            + " PRECEDING AND "
            + range_max
            + " FOLLOWING "
            + ") AS "
            + quote_column(window.name)
        )

    def _normalize_select(self, select) -> SelectOp:
        return normalize_one(select)

    def transaction(self):
        """
        PERFORM MULTIPLE ACTIONS IN A TRANSACTION
        """
        return Transaction(self)


class Transaction:
    def __init__(self, table):
        self.transaction = None
        self.table = table

    def __enter__(self):
        self.transaction = self.container.db.transaction()
        self.table.db = self.transaction  # REDIRECT SQL TO TRANSACTION
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.table.db = self.table.container.db
        self.transaction.__exit__(exc_type, exc_val, exc_tb)
        self.transaction = None

    def __getattr__(self, item):
        return getattr(self.table, item)


type2container["sqlite"] = QueryTable

export("jx_sqlite.expressions.nested_op", QueryTable)
export("jx_sqlite.models.container", QueryTable)