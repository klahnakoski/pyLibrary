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

import mo_math
from jx_base.expressions import (
    ToBooleanOp,
    NULL,
    Literal,
    MinOp,
    FALSE,
    SelectOp,
    WhenOp,
    CaseOp, CountOp, PercentileOp, CardinalityOp, OrOp, AndOp, UnionOp, MaxOp,
)
from jx_base.language import is_op
from jx_python import jx
from jx_sqlite.expressions._utils import (
    SQLang,
    sql_type_key_to_json_type,
)
from jx_sqlite.expressions.tuple_op import TupleOp
from jx_sqlite.expressions.variable import Variable
from jx_sqlite.setop_table import SetOpTable
from jx_sqlite.sqlite import *
from jx_sqlite.sqlite import quote_column, quote_value, sql_alias
from jx_sqlite.utils import (
    ColumnMapping,
    STATS,
    _make_column_name,
    get_column,
    sql_aggs,
    sql_text_array_to_set,
    untyped_column,
    PARENT,
    UID,
    DIGITS_TABLE,
    table_alias,
)
from mo_dots import (
    coalesce,
    concat_field,
    startswith_field,
    to_data,
    is_missing,
    Null,
)
from mo_future import text
from mo_json import (
    NUMBER, T_BOOLEAN,
    jx_type_to_json_type,
)
from mo_logs import Log

EXISTS_COLUMN = quote_column("__exists__")


class EdgesTable(SetOpTable):
    def _edges_op(self, query, schema):
        query = query.copy()  # WE WILL BE MARKING UP THE QUERY
        index_to_column = {}  # MAP FROM INDEX TO COLUMN (OR SELECT CLAUSE)
        outer_selects = []  # EVERY SELECT CLAUSE (NOT TO BE USED ON ALL TABLES, OF COURSE)
        base_table, path = schema.snowflake.fact_name, schema.nested_path
        nest_to_alias = {
            nested_path: table_alias(i)
            for i, (nested_path, sub_table) in enumerate(self.snowflake.tables)
        }

        tables = []
        for n, a in nest_to_alias.items():
            if startswith_field(path[0], n):
                tables.append({"nest": n, "alias": a})
        tables = jx.sort(tables, {"value": {"length": "nest"}})

        from_sql = [sql_alias(
            quote_column(concat_field(base_table, tables[0].nest)), tables[0].alias
        )]
        for previous, t in zip(tables, tables[1::]):
            from_sql.append(ConcatSQL(
                SQL_LEFT_JOIN,
                sql_alias(quote_column(concat_field(base_table, t.nest)), t.alias),
                SQL_ON,
                quote_column(t.alias, PARENT),
                SQL_EQ,
                quote_column(previous.alias, UID),
            ))

        main_filter = ToBooleanOp(query.where).partial_eval(SQLang).to_sql(schema).frum

        column_index = 0
        edge_names = []
        all_domain_names = []
        ons = []
        join_types = []
        groupby = []
        orderby = []
        inner_domains = []
        outer_domains = []

        select_clause = [ConcatSQL(SQL_ONE, SQL_AS, EXISTS_COLUMN)] + [
            quote_column(c.es_column) for c in self.snowflake.columns
        ]

        for edge_index, query_edge in enumerate(query.edges):
            domain_aliases = []

            def get_domain_alias(c):
                return "d" + text(edge_index) + "c" + text(c)

            edge_alias = "e" + text(edge_index)
            edge_names.append(edge_alias)
            query_edge_domain = query_edge.domain
            ###################################################################
            # DOMAIN
            ###################################################################
            if query_edge_domain.type == "set":
                domain_alias = get_domain_alias(column_index)
                domain_aliases.append(domain_alias)
                column_index += 1

                if query_edge.value:
                    edge_sql = query_edge.value.partial_eval(SQLang).to_sql(schema)
                    domains_sql = SQL_UNION_ALL.join(
                        ConcatSQL(
                            SQL_SELECT,
                            sql_alias(
                                quote_value(coalesce(p.dataIndex, i)), domain_alias
                            ),
                            SQL_COMMA,
                            sql_alias(quote_value(p.value), domain_alias + "v"),
                        )
                        for i, p in enumerate(query_edge_domain.partitions)
                    )
                    join_type = (
                        SQL_LEFT_JOIN if query_edge.allowNulls else SQL_INNER_JOIN
                    )
                    on_clause = ConcatSQL(
                        quote_column(edge_alias, domain_alias + "v"), SQL_EQ, edge_sql,
                    )
                elif any(p.where for p in query_edge_domain.partitions):
                    if not all(p.where for p in query_edge_domain.partitions):
                        Log.error("expecting all partitions to have `where` clause")

                    domains_sql = SQL_UNION_ALL.join(
                        ConcatSQL(
                            SQL_SELECT,
                            sql_alias(
                                quote_value(coalesce(p.dataIndex, i)), domain_alias
                            ),
                        )
                        for i, p in enumerate(query_edge_domain.partitions)
                    )
                    join_type = (
                        SQL_LEFT_JOIN if query_edge.allowNulls else SQL_INNER_JOIN
                    )
                    on_clause = ConcatSQL(
                        quote_column(edge_alias, domain_alias),
                        SQL_EQ,
                        CaseOp([
                            WhenOp(p.where, then=Literal(p.dataIndex))
                            for p in query_edge_domain.partitions
                        ])
                        .partial_eval(SQLang)
                        .to_sql(schema),
                    )
                else:
                    raise Log.error("do not know what to do")

                num_sql_columns = len(index_to_column)

                index_to_column[num_sql_columns] = ColumnMapping(
                    is_edge=True,
                    push_list_name=query_edge.name,
                    push_column_name=query_edge.name,
                    push_column_index=edge_index,
                    push_column_child=".",
                    pull=get_pull_func(num_sql_columns, query_edge_domain),
                    type=NUMBER,
                    sql=FALSE.to_sql(schema),
                    column_alias=domain_alias,
                )

            elif query_edge_domain.type == "default":
                edge_sql = query_edge.value.partial_eval(SQLang).to_sql(schema)

                if is_op(edge_sql.frum, TupleOp):
                    domain_aliases = [
                        get_domain_alias(column_index + i)
                        for i, term in enumerate(edge_sql.frum.terms)
                    ]
                    select_columns = sql_list([
                        sql_alias(term.to_sql(schema), domain_alias)
                        for domain_alias, term in zip(
                            domain_aliases, edge_sql.frum.terms
                        )
                    ])
                    where_columns = SQL_OR.join([
                        ConcatSQL(quote_column(domain_alias), SQL_IS_NOT_NULL)
                        for domain_alias in domain_aliases
                    ])
                    groupby_columns = sql_list([
                        quote_column(domain_alias) for domain_alias in domain_aliases
                    ])
                    orderby_columns = sql_list([
                        quote_column(domain_alias) for domain_alias in domain_aliases
                    ])
                    on_clause = SQL_AND.join([
                        sql_iso(
                            quote_column(edge_alias, domain_alias),
                            SQL_EQ,
                            term.to_sql(schema),
                            SQL_OR,
                            quote_column(edge_alias, domain_alias),
                            SQL_IS_NULL,
                            SQL_AND,
                            term.to_sql(schema),
                            SQL_IS_NULL,
                        )
                        for domain_alias, term in zip(
                            domain_aliases, edge_sql.frum.terms
                        )
                    ])

                    for i, term in enumerate(edge_sql.frum.terms):
                        index_to_column[column_index + i] = ColumnMapping(
                            is_edge=True,
                            push_list_name=query_edge.name,
                            push_column_name=query_edge.name,
                            push_column_index=edge_index,
                            num_push_columns=len(query_edge.value.terms),
                            push_column_child=i,
                            pull=get_pull_func(column_index + i),
                            type=jx_type_to_json_type(term.type),
                            sql=FALSE.to_sql(schema),
                            column_alias=get_domain_alias(column_index + i),
                        )
                    column_index += len(edge_sql.frum.terms)
                elif is_op(edge_sql.frum, SelectOp):
                    domain_aliases = [
                        get_domain_alias(column_index + i)
                        for i, term in enumerate(edge_sql.frum.terms)
                    ]
                    select_columns = sql_list([
                        sql_alias(term["value"].to_sql(schema), domain_alias)
                        for domain_alias, term in zip(
                            domain_aliases, edge_sql.frum.terms
                        )
                    ])
                    where_columns = SQL_OR.join([
                        ConcatSQL(quote_column(domain_alias), SQL_IS_NOT_NULL)
                        for domain_alias in domain_aliases
                    ])
                    groupby_columns = sql_list([
                        quote_column(domain_alias) for domain_alias in domain_aliases
                    ])
                    orderby_columns = sql_list([
                        quote_column(domain_alias) for domain_alias in domain_aliases
                    ])
                    on_clause = SQL_AND.join([
                        sql_iso(
                            quote_column(edge_alias, domain_alias),
                            SQL_EQ,
                            term["value"].to_sql(schema),
                            SQL_OR,
                            quote_column(edge_alias, domain_alias),
                            SQL_IS_NULL,
                            SQL_AND,
                            term["value"].to_sql(schema),
                            SQL_IS_NULL,
                        )
                        for domain_alias, term in zip(
                            domain_aliases, edge_sql.frum.terms
                        )
                    ])
                    for i, term in enumerate(edge_sql.frum.terms):
                        index_to_column[column_index + i] = ColumnMapping(
                            is_edge=True,
                            push_list_name=query_edge.name,
                            push_column_name=query_edge.name,
                            push_column_index=edge_index,
                            push_column_child=term["name"],
                            pull=get_pull_func(column_index + i),
                            type=jx_type_to_json_type(term.type),
                            sql=FALSE.to_sql(schema),
                            column_alias=get_domain_alias(column_index + i),
                        )
                    column_index += len(edge_sql.frum.terms)
                else:
                    domain_alias = get_domain_alias(column_index)
                    domain_aliases.append(domain_alias)
                    select_columns = sql_alias(edge_sql, domain_alias)
                    column_index += 1
                    where_columns = ConcatSQL(
                        quote_column(domain_alias), SQL_IS_NOT_NULL
                    )
                    groupby_columns = quote_column(domain_alias)
                    orderby_columns = quote_column(domain_alias)
                    on_clause = ConcatSQL(
                        quote_column(edge_alias, domain_alias), SQL_EQ, edge_sql
                    )
                    num_sql_columns = len(index_to_column)

                    index_to_column[num_sql_columns] = ColumnMapping(
                        is_edge=True,
                        push_list_name=query_edge.name,
                        push_column_name=query_edge.name,
                        push_column_index=edge_index,
                        push_column_child=".",
                        pull=get_pull_func(num_sql_columns, query_edge_domain),
                        type=NUMBER,
                        sql=FALSE.to_sql(schema),
                        column_alias=domain_alias,
                    )

                limit = (
                    MinOp([query.limit, query_edge_domain.limit])
                    .partial_eval(SQLang)
                    .to_sql(schema)
                )

                domains_sql = ConcatSQL(
                    SQL_SELECT,
                    sql_alias(sql_count(SQL_ONE), "num"),
                    SQL_COMMA,
                    select_columns,
                    SQL_FROM,
                    ConcatSQL(*from_sql),
                    SQL_WHERE,
                    where_columns,
                    SQL_GROUPBY,
                    groupby_columns,
                    SQL_ORDERBY,
                    sql_count(SQL_ONE),
                    SQL_DESC,
                    SQL_COMMA,
                    orderby_columns,
                    SQL_LIMIT,
                    limit,
                )

                join_type = SQL_LEFT_JOIN if query_edge.allowNulls else SQL_INNER_JOIN
            elif query_edge_domain.type in ("duration", "time", "range"):
                domain_alias = get_domain_alias(column_index)
                domain_aliases.append(domain_alias)
                column_index += 1

                if query_edge.value:
                    edge_sql = query_edge.value.partial_eval(SQLang).to_sql(schema)
                    domains_sql = range_sql(
                        domain=query_edge_domain,
                        min_value_name=domain_alias + "v",
                        max_value_name=domain_alias + "max",
                        index_name=domain_alias,
                    )
                    limit = (
                        MinOp([query.limit, query_edge_domain.limit])
                        .partial_eval(SQLang)
                        .to_sql(schema)
                    )
                    if limit is not NULL:
                        domains_sql = ConcatSQL(domains_sql, SQL_LIMIT, limit)
                    join_type = (
                        SQL_LEFT_JOIN if query_edge.allowNulls else SQL_INNER_JOIN
                    )
                    on_clause = ConcatSQL(
                        quote_column(edge_alias, domain_alias + "v"),
                        SQL_LE,
                        edge_sql,
                        SQL_AND,
                        edge_sql,
                        SQL_LT,
                        quote_column(edge_alias, domain_alias + "max"),
                    )
                elif query_edge.range:
                    min_sql = query_edge.range.min.partial_eval(SQLang).to_sql(schema)
                    max_sql = query_edge.range.max.partial_eval(SQLang).to_sql(schema)
                    domains_sql = range_sql(
                        domain=query_edge_domain,
                        min_value_name=domain_alias + "v",
                        max_value_name=domain_alias + "max",
                        index_name=domain_alias,
                    )
                    limit = (
                        MinOp([query.limit, query_edge_domain.limit])
                        .partial_eval(SQLang)
                        .to_sql(schema)
                    )
                    domains_sql = ConcatSQL(domains_sql, SQL_LIMIT, limit,)
                    join_type = SQL_INNER_JOIN
                    on_clause = ConcatSQL(
                        quote_column(edge_alias, domain_alias + "v"),
                        SQL_LT,
                        max_sql,
                        SQL_AND,
                        min_sql,
                        SQL_LT,
                        quote_column(edge_alias, domain_alias + "max"),
                    )
                else:
                    raise Log.error("do not know how to handle")

                num_sql_columns = len(index_to_column)

                index_to_column[num_sql_columns] = ColumnMapping(
                    is_edge=True,
                    push_list_name=query_edge.name,
                    push_column_name=query_edge.name,
                    push_column_index=edge_index,
                    push_column_child=".",
                    pull=get_pull_func(num_sql_columns, query_edge_domain),
                    type=NUMBER,
                    sql=FALSE.to_sql(schema),
                    column_alias=domain_alias,
                )
            else:
                raise Log.error("not handled")

            ###################################################################
            # AGGREGATE CLAUSE PARTS
            ###################################################################

            all_domain_names.append(domain_aliases)
            inner_domains.append(domains_sql)
            if query_edge.allowNulls:
                outer_domains.append(ConcatSQL(
                    SQL_SELECT,
                    sql_list([
                        quote_column(domain_alias) for domain_alias in domain_aliases
                    ]),
                    SQL_FROM,
                    sql_iso(domains_sql),
                    SQL_UNION_ALL,
                    SQL_SELECT,
                    sql_list([SQL_NULL for _ in domain_aliases]),
                ))
            else:
                outer_domains.append(domains_sql)

            ons.append(on_clause)
            join_types.append(join_type)

            groupby.append(sql_list([
                quote_column(edge_alias, domain_alias)
                for domain_alias in domain_aliases
            ]))

            full_domain_aliases = [
                quote_column(edge_alias, domain_alias)
                for domain_alias in domain_aliases
            ]
            outer_selects.extend([
                sql_alias(full_domain_alias, domain_alias)
                for full_domain_alias, domain_alias in zip(
                    full_domain_aliases, domain_aliases
                )
            ])

            for full_domain_alias in full_domain_aliases:
                orderby.append(ConcatSQL(full_domain_alias, SQL_IS_NULL))
                if hasattr(query_edge_domain, "sort") and query_edge_domain.sort == -1:
                    orderby.append(full_domain_alias + SQL_DESC)
                else:
                    orderby.append(full_domain_alias)

        ###################################################################
        # AGGREGATE CLAUSE PARTS
        ###################################################################
        offset = len(query.edges)
        self.aggregates(index_to_column, offset, outer_selects, query, schema)

        for w in query.window:
            outer_selects.append(self._window_op(self, query, w))

        facts = sql_alias(
            sql_iso(
                SQL_SELECT,
                sql_list(select_clause),
                SQL_FROM,
                ConcatSQL(*from_sql),
                SQL_WHERE,
                main_filter,
            ),
            nest_to_alias["."],
        )

        edge_sql = []
        for edge_index, query_edge in enumerate(query.edges):
            edge_alias = "e" + text(edge_index)
            domains_sql = inner_domains[edge_index]
            edge_sql.append(sql_alias(sql_iso(domains_sql), edge_alias))

        # COORDINATES OF ALL primary DATA
        clauses = [ConcatSQL(SQL_SELECT, sql_list(outer_selects), SQL_FROM, facts)]
        for t, s, j in zip(join_types, edge_sql, ons):
            clauses.append(ConcatSQL(t, s, SQL_ON, j))
        if groupby:
            clauses.append(ConcatSQL(SQL_GROUPBY, sql_list(groupby)))
        command = ConcatSQL(*clauses)

        # ALL COORDINATES MISSED BY primary DATA
        if query.edges:
            clauses = [ConcatSQL(
                SQL_SELECT,
                sql_list([
                    quote_column(
                        "e" + text(i.push_column_index) if i.is_edge else "p",
                        i.column_alias,
                    )
                    for i in index_to_column.values()
                ]),
                SQL_FROM,
                sql_iso(outer_domains[0]),
                SQL_AS,
                quote_column(edge_names[0]),
            )]
            for edge_name, outer_domain in zip(edge_names[1:], outer_domains[1:]):
                clauses.append(ConcatSQL(
                    SQL_LEFT_JOIN,
                    sql_iso(outer_domain),
                    SQL_AS,
                    quote_column(edge_name),
                    SQL_ON,
                    SQL_TRUE,
                ))
            clauses.append(ConcatSQL(
                SQL_LEFT_JOIN,
                sql_iso(command),
                SQL_AS,
                quote_column("p"),
                SQL_ON,
                SQL_AND.join(
                    sql_iso(ConcatSQL(
                        quote_column("p", d),
                        SQL_EQ,
                        quote_column(e, d),
                        SQL_OR,
                        quote_column("p", d),
                        SQL_IS_NULL,
                        SQL_AND,
                        quote_column(e, d),
                        SQL_IS_NULL,
                    ))
                    for e, domain_aliases in zip(edge_names, all_domain_names)
                    for d in domain_aliases
                ),
            ))
            command = ConcatSQL(*clauses)

        if orderby:
            command = ConcatSQL(command, SQL_ORDERBY, sql_list(orderby))

        return command, index_to_column

    def aggregates(self, index_to_column, offset, outer_selects, query, schema):
        for ssi, s in enumerate(to_data(query.select.terms)):
            si = ssi + offset
            if (
                is_op(s.value, Variable)
                and s.value.var == "."
                and is_op(s.aggregate, CountOp)
            ):
                # COUNT RECORDS, NOT ANY ONE VALUE
                sql = sql_alias(sql_count(EXISTS_COLUMN), s.name)

                column_number = len(outer_selects)
                outer_selects.append(sql)
                index_to_column[column_number] = ColumnMapping(
                    push_list_name=s.name,
                    push_column_name=s.name,
                    push_column_index=si,
                    push_column_child=".",
                    pull=get_column(column_number, None, s.aggregate.default.value),
                    sql=sql,
                    column_alias=s.name,
                    type=NUMBER,
                )
            elif is_op(s.aggregate, CountOp) and (not query.edges and not query.groupby):
                value = s.value.var
                columns = [
                    c.es_column
                    for c in self.snowflake.columns
                    if untyped_column(c.es_column)[0] == value
                ]
                sql = SQL("+").join(sql_count(quote_column(col)) for col in columns)
                column_number = len(outer_selects)
                outer_selects.append(sql_alias(sql, _make_column_name(column_number)))
                index_to_column[column_number] = ColumnMapping(
                    push_list_name=s.name,
                    push_column_name=s.name,
                    push_column_index=si,
                    push_column_child=".",
                    pull=get_column(column_number, None, s.aggregate.default.value),
                    sql=sql,
                    column_alias=_make_column_name(column_number),
                    type=sql_type_key_to_json_type["n"],
                )
            elif is_op(s.aggregate, PercentileOp):
                raise NotImplementedError()
            elif is_op(s.aggregate, CardinalityOp):
                sql = s.value.partial_eval(SQLang).to_sql(schema)
                column_number = len(outer_selects)
                count_sql = sql_alias(
                    sql_count("DISTINCT" + sql_iso(sql)),
                    _make_column_name(column_number),
                )
                outer_selects.append(count_sql)
                index_to_column[column_number] = ColumnMapping(
                    push_list_name=s.name,
                    push_column_name=s.name,
                    push_column_index=si,
                    push_column_child=".",
                    pull=get_column(column_number, None, s.aggregate.default.value),
                    sql=count_sql,
                    column_alias=_make_column_name(column_number),
                    type=NUMBER,
                )
            elif is_op(s.aggregate, OrOp):
                sql = s.value.partial_eval(SQLang).to_sql(schema)
                column_number = len(outer_selects)
                outer_selects.append(sql_alias(
                    ConcatSQL(SQL_NOT, SQL_NOT, sql_call("SUM", sql_iso(sql))),
                    _make_column_name(column_number),
                ))
                index_to_column[column_number] = ColumnMapping(
                    push_list_name=s.name,
                    push_column_name=s.name,
                    push_column_index=si,
                    push_column_child=".",
                    pull=get_column(column_number, T_BOOLEAN, s.aggregate.default.value),
                    sql=sql,
                    column_alias=_make_column_name(column_number),
                    type=BOOLEAN
                )
            elif is_op(s.aggregate, AndOp):
                sql = s.value.partial_eval(SQLang).to_sql(schema)
                column_number = len(outer_selects)
                outer_selects.append(sql_alias(
                    ConcatSQL(SQL_NOT, sql_call("SUM", sql_iso(ConcatSQL(SQL_NOT, sql_iso(sql))))),
                    _make_column_name(column_number),
                ))
                index_to_column[column_number] = ColumnMapping(
                    push_list_name=s.name,
                    push_column_name=s.name,
                    push_column_index=si,
                    push_column_child=".",
                    pull=get_column(column_number, T_BOOLEAN, s.aggregate.default.value),
                    sql=sql,
                    column_alias=_make_column_name(column_number),
                    type=BOOLEAN
                )
            elif is_op(s.aggregate, UnionOp):
                for details in s.value.partial_eval(SQLang).to_sql(schema):
                    for sql_type, sql in details.sql.items():
                        column_number = len(outer_selects)
                        outer_selects.append(sql_alias(
                            "JSON_GROUP_ARRAY(DISTINCT" + sql_iso(sql) + ")",
                            _make_column_name(column_number),
                        ))
                        index_to_column[column_number] = ColumnMapping(
                            push_list_name=s.name,
                            push_column_name=s.name,
                            push_column_index=si,
                            push_column_child=".",
                            pull=sql_text_array_to_set(column_number),
                            sql=sql,
                            column_alias=_make_column_name(column_number),
                            type=sql_type_key_to_json_type[sql_type],
                        )
            elif s.aggregate == "stats":  # THE STATS OBJECT
                sql = s.value.to_sql(schema)
                for name, code in STATS.items():
                    full_sql = code.replace("{{value}}", sql)
                    column_number = len(outer_selects)
                    outer_selects.append(sql_alias(
                        full_sql, _make_column_name(column_number)
                    ))
                    index_to_column[column_number] = ColumnMapping(
                        push_list_name=s.name,
                        push_column_name=s.name,
                        push_column_index=si,
                        push_column_child=name,
                        pull=get_column(column_number, None, s.aggregate.default.value),
                        sql=full_sql,
                        column_alias=_make_column_name(column_number),
                        type="number",
                    )
            else:  # STANDARD AGGREGATES
                sql = s.value.partial_eval(SQLang).to_sql(schema)
                sql = sql_call(sql_aggs[s.aggregate.op], sql)
                data_type = jx_type_to_json_type(s.aggregate.type)

                if s.aggregate.default is not NULL:
                    sql = sql_coalesce([sql, s.aggregate.default.to_sql(schema)])
                column_number = len(outer_selects)
                outer_selects.append(sql_alias(sql, _make_column_name(column_number)))
                index_to_column[column_number] = ColumnMapping(
                    push_list_name=s.name,
                    push_column_name=s.name,
                    push_column_index=si,
                    push_column_child=".",
                    pull=get_column(column_number, data_type, s.aggregate.default.value),
                    sql=sql,
                    column_alias=_make_column_name(column_number),
                    type=data_type
                )


def range_sql(domain, min_value_name, max_value_name, index_name):
    if domain.interval == None:
        # IRREGULAR RANGE, SPECIFIC PARTITIONS EXPECTED
        return SQL_UNION_ALL.join(
            ConcatSQL(
                SQL_SELECT,
                sql_alias(quote_value(part.min), min_value_name),
                SQL_COMMA,
                sql_alias(quote_value(part.max), max_value_name),
                SQL_COMMA,
                sql_alias(quote_value(part.dataIndex), index_name),
            )
            for part in domain.partitions
        )

    width = (domain.max - domain.min) / domain.interval
    digits = mo_math.floor(mo_math.log10(width - 1))
    if digits == 0:
        rownum_sql = quote_column("a", "value")
    else:
        rownum_sql = SQL_PLUS.join(
            ConcatSQL(
                quote_value(pow(10, j)),
                SQL_STAR,
                quote_column(text(chr(ord(b"a") + j)), "value"),
            )
            for j in range(digits + 1)
        )

    if domain.interval == 1:
        if domain.min == 0:
            domain = ConcatSQL(
                SQL_SELECT,
                sql_list([
                    sql_alias(rownum_sql, index_name),
                    sql_alias(rownum_sql, min_value_name),
                    sql_alias(ConcatSQL(rownum_sql, SQL_PLUS, SQL_ONE), max_value_name),
                ]),
                SQL_FROM,
                sql_alias(quote_column(DIGITS_TABLE), "a"),
            )
        else:
            domain = ConcatSQL(
                SQL_SELECT,
                sql_list([
                    sql_alias(rownum_sql, index_name),
                    sql_alias(
                        ConcatSQL(rownum_sql, SQL_PLUS, quote_value(domain.min)),
                        min_value_name,
                    ),
                    sql_alias(
                        ConcatSQL(rownum_sql, SQL_PLUS, quote_value(domain.min + 1)),
                        max_value_name,
                    ),
                ]),
                SQL_FROM,
                sql_alias(quote_column(DIGITS_TABLE), "a"),
            )
    else:
        if domain.min == 0:
            domain = ConcatSQL(
                SQL_SELECT,
                sql_list([
                    sql_alias(rownum_sql, index_name),
                    sql_alias(
                        ConcatSQL(rownum_sql, SQL_STAR, quote_value(domain.interval)),
                        min_value_name,
                    ),
                    sql_alias(
                        ConcatSQL(
                            rownum_sql,
                            SQL_STAR,
                            quote_value(domain.interval),
                            SQL_PLUS,
                            quote_value(domain.interval),
                        ),
                        max_value_name,
                    ),
                ]),
                SQL_FROM,
                sql_alias(quote_column(DIGITS_TABLE), "a"),
            )
        else:
            domain = ConcatSQL(
                SQL_SELECT,
                sql_list([
                    sql_alias(rownum_sql, index_name),
                    sql_alias(
                        ConcatSQL(
                            sql_iso(rownum_sql, SQL_STAR, quote_value(domain.interval)),
                            SQL_PLUS,
                            quote_value(domain.min),
                        ),
                        min_value_name,
                    ),
                    sql_alias(
                        ConcatSQL(
                            sql_iso(rownum_sql, SQL_STAR, quote_value(domain.interval)),
                            SQL_PLUS,
                            quote_value(domain.min + domain.interval),
                        ),
                        max_value_name,
                    ),
                ]),
                SQL_FROM,
                sql_alias(quote_column(DIGITS_TABLE), "a"),
            )

    for j in range(digits):
        domain = ConcatSQL(
            domain,
            SQL_INNER_JOIN,
            sql_alias(quote_column(DIGITS_TABLE), text(chr(ord(b"a") + j + 1))),
            SQL_ON,
            SQL_TRUE,
        )
    domain = ConcatSQL(
        domain,
        SQL_WHERE,
        rownum_sql,
        SQL_LT,
        quote_value(width),
        SQL_ORDERBY,
        quote_column(index_name),
    )
    return domain


def get_pull_func(column, domain=None):
    if domain is None:

        def simple_pull_func(row):
            value = row[column]
            if is_missing(value):
                return Null
            return value

        return simple_pull_func
    else:

        def pull_func(row):
            index = row[column]
            if is_missing(index):
                return Null
            # TODO: OPPORTUNITY TO RETURN DOMAIN OBJECT, NOT JUST KEY VALUE
            return domain.getKeyByIndex(index)

        return pull_func
