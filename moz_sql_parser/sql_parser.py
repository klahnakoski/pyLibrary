# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_parsing import whitespaces
from mo_parsing.whitespaces import NO_WHITESPACE, Whitespace

from mo_sql_parsing import utils
from mo_sql_parsing.keywords import *
from mo_sql_parsing.types import get_column_type, time_functions
from mo_sql_parsing.utils import *
from mo_sql_parsing.windows import window


def no_dashes(tokens, start, string):
    if "-" in tokens[0]:
        index = tokens[0].find("-")
        raise ParseException(
            tokens.type,
            start + index + 1,  # +1 TO ENSURE THIS MESSAGE HAS PRIORITY
            string,
            """Ambiguity: Use backticks (``) around identifiers with dashes, or add space around subtraction operator.""",
        )


digit = Char("0123456789")
with whitespaces.NO_WHITESPACE:
    ident_w_dash = (
        Char(FIRST_IDENT_CHAR)
        + (Regex("(?<=[^ 0-9])\\-(?=[^ 0-9])") | Char(IDENT_CHAR))[...]
    )
    ident_w_dash = Regex(ident_w_dash.__regex__()[1]) / no_dashes

simple_ident = Word(FIRST_IDENT_CHAR, IDENT_CHAR)


def common_parser():
    atomic_ident = ansi_ident | mysql_backtick_ident | simple_ident
    return parser(regex_string | ansi_string, atomic_ident)


def mysql_parser():
    utils.emit_warning_for_double_quotes = False

    mysql_string = regex_string | ansi_string | mysql_doublequote_string
    atomic_ident = mysql_backtick_ident | sqlserver_ident | ident_w_dash
    return parser(mysql_string, atomic_ident)


def sqlserver_parser():
    atomic_ident = ansi_ident | mysql_backtick_ident | sqlserver_ident | simple_ident
    return parser(regex_string | ansi_string, atomic_ident, sqlserver=True)


def parser(literal_string, simple_ident, sqlserver=False):
    ident = Combine(delimited_list(simple_ident, separator=".", combine=True))

    with Whitespace() as white:
        rest_of_line = Regex(r"[^\n]*")

        white.add_ignore(Literal("--") + rest_of_line)
        white.add_ignore(Literal("#") + rest_of_line)
        white.add_ignore(Literal("/*") + SkipTo("*/", include=True))

        with whitespaces.NO_WHITESPACE:
            identifier = ~RESERVED + ident
        function_name = ~FROM + ident

        # EXPRESSIONS
        expression = Forward()
        (
            column_type,
            column_definition,
            column_def_references,
            column_option,
        ) = get_column_type(expression, identifier, literal_string)

        # CASE
        case = (
            CASE
            + Group(ZeroOrMore(
                (WHEN + expression("when") + THEN + expression("then")) / to_when_call
            ))("case")
            + Optional(ELSE + expression("else"))
            + END
        ) / to_case_call

        switch = (
            CASE
            + expression("value")
            + Group(ZeroOrMore(
                (WHEN + expression("when") + THEN + expression("then")) / to_when_call
            ))("case")
            + Optional(ELSE + expression("else"))
            + END
        ) / to_switch_call

        cast = (
            Group(
                CAST("op") + LB + expression("params") + AS + column_type("params") + RB
            )
            / to_json_call
        )

        substring = (
            Group(
                keyword("substring")("op")
                + LB
                + expression("params")
                + Optional(assign("from", expression))
                + Optional(assign("for", expression))
                + RB
            )
            / to_json_call
        )

        # TODO: CAN THIS BE MERGED WITH cast?  DOES THE REGEX OPTIMIZATION BREAK?
        safe_cast = (
            Group(
                SAFE_CAST("op")
                + LB
                + expression("params")
                + AS
                + column_type("params")
                + RB
            )
            / to_json_call
        )

        trim = (
            Group(
                keyword("trim").suppress()
                + LB
                + Optional(
                    (keyword("both") | keyword("trailing") | keyword("leading"))
                    / (lambda t: t[0].lower())
                )("direction")
                + (
                    assign("from", expression)
                    | expression("chars") + Optional(assign("from", expression))
                )
                + RB
            )
            / to_trim_call
        )

        _standard_time_intervals = MatchFirst([
            keyword(d) / (lambda t: durations[t[0].lower()]) for d in durations.keys()
        ]).set_parser_name("duration")("params")

        duration = expression("params") + _standard_time_intervals

        literal_duration = (real_num | int_num)("params") + _standard_time_intervals

        interval = (
            INTERVAL + ("'" + delimited_list(literal_duration) + "'" | duration)
        ) / to_interval_call

        timestamp = (
            time_functions("op")
            + (
                literal_string("params")
                | MatchFirst([
                    keyword(t) / (lambda t: t.lower()) for t in times
                ])("params")
            )
        ) / to_json_call

        extract = (
            keyword("extract")("op")
            + LB
            + (_standard_time_intervals | expression("params"))
            + FROM
            + expression("params")
            + RB
        ) / to_json_call

        alias = Optional((
            (
                (
                    AS
                    + (
                        identifier("name")
                        + Optional(LB + delimited_list(ident("col")) + RB)
                    )
                    | (
                        identifier("name")
                        + Optional(
                            (LB + delimited_list(ident("col")) + RB)
                            | (AS + delimited_list(identifier("col")))
                        )
                    )
                )
                + ~FollowedBy(LB)  # THIS IS NOT AN ALIAS
            )
            / to_alias
        )("name"))

        named_column = Group(Group(expression)("value") + alias)

        stack = (
            keyword("stack")("op")
            + LB
            + int_num("width")
            + ","
            + delimited_list(expression)("args")
            + RB
        ) / to_stack

        # ARRAY[foo],
        # ARRAY < STRING > [foo, bar], INVALID
        # ARRAY < STRING > [foo, bar],
        create_array = (
            keyword("array")("op")
            + Optional(LT.suppress() + column_type("type") + GT.suppress())
            + (
                LB + delimited_list(Group(expression))("args") + RB
                | (
                    Literal("[")
                    + Optional(delimited_list(Group(expression))("args"))
                    + Literal("]")
                )
            )
        )

        if not sqlserver:
            # SQL SERVER DOES NOT SUPPORT [] FOR ARRAY CONSTRUCTION (USED FOR IDENTIFIERS)
            create_array = (
                Literal("[") + delimited_list(Group(expression))("args") + Literal("]")
                | create_array
            )

        create_array = create_array / to_array

        create_map = (
            keyword("map")
            + Literal("[")
            + expression("keys")
            + ","
            + expression("values")
            + Literal("]")
        ) / to_map

        create_struct = (
            keyword("struct")("op")
            + Optional(
                LT.suppress() + delimited_list(column_type)("types") + GT.suppress()
            )
            + LB
            + delimited_list(Group(
                (expression("value") + alias) / to_select_call
            ))("args")
            + RB
        ) / to_struct

        distinct = (
            DISTINCT("op") + delimited_list(named_column)("params")
        ) / to_json_call

        query = Forward()

        sort_column = (
            expression("value").set_parser_name("sort1")
            + Optional(DESC("sort") | ASC("sort"))
            + Optional(assign("nulls", keyword("first") | keyword("last")))
        )

        one_param = (
            # KEYWORD PARAMETERS?
            # https://docs.snowflake.com/en/sql-reference/functions/generator.html
            Group(ident + Literal("=>").suppress() + Group(expression))("kwargs")
            / to_kwarg
        ) | Group(expression)("params")

        call_function = (
            function_name("op")
            + LB
            + Optional(Group(query)("params") | delimited_list(one_param))
            + Optional(
                (keyword("respect") | keyword("ignore"))("nulls")
                + keyword("nulls").suppress()
            )
            + Optional(ORDER_BY + delimited_list(Group(sort_column))("orderby"))
            + RB
        ) / to_json_call

        dynamic_accessor = (
            Literal("[").suppress() + expression + Literal("]").suppress()
        )
        simple_accessor = Literal(".").suppress() + simple_ident / to_literal
        accessor = (
            Literal(":").suppress()
            + Group(simple_ident / to_literal | dynamic_accessor)
            + ZeroOrMore(Group(simple_accessor | dynamic_accessor))
        )

        with NO_WHITESPACE:

            def scale(tokens):
                return {"mul": [tokens[0], tokens[1]]}

            scale_function = ((real_num | int_num) + call_function) / scale
            scale_ident = ((real_num | int_num) + ident) / scale

        compound = (
            NULL
            | TRUE
            | FALSE
            | NOCASE
            | interval
            | timestamp
            | extract
            | case
            | switch
            | cast
            | substring
            | safe_cast
            | distinct
            | trim
            | stack
            | create_array
            | create_map
            | create_struct
            | (LB + Group(query) + RB)
            | (LB + Group(delimited_list(expression)) / to_tuple_call + RB)
            | literal_string
            | hex_num
            | scale_function
            | scale_ident
            | real_num
            | int_num
            | call_function
            | Combine(identifier + Optional(".*"))
        )

        window_clause, over_clause = window(expression, identifier, sort_column)

        expression << (
            (
                Literal("*")
                | infix_notation(
                    compound,
                    [
                        (dynamic_accessor, 1, LEFT_ASSOC, to_offset,),
                        (simple_accessor, 1, LEFT_ASSOC, to_offset,),
                        (accessor, 1, LEFT_ASSOC, to_offset),
                        (window_clause, 1, LEFT_ASSOC, to_window_mod),
                        (
                            assign("filter", LB + WHERE + expression + RB),
                            1,
                            LEFT_ASSOC,
                            to_window_mod,
                        ),
                    ]
                    + [
                        (
                            o,
                            1 if o in unary_ops else (3 if isinstance(o, tuple) else 2),
                            unary_ops.get(o, LEFT_ASSOC),
                            to_lambda if o is LAMBDA else to_json_operator,
                        )
                        for o in KNOWN_OPS
                    ],
                )
            )("value").set_parser_name("expression")
        )

        select_column = (
            Group(expression("value") + alias | Literal("*")("value")) / to_select_call
        )

        table_source = Forward()

        pivot_join = (
            PIVOT("op")
            + (
                LB
                + expression("aggregate")
                + assign("for", identifier)
                + (IN + expression("in"))
                + RB
                + alias
            )("kwargs")
        ) / to_pivot_call

        unpivot_join = (
            UNPIVOT("op")
            + (
                LB
                + (expression("value") + assign("for", identifier) + IN)
                + (LB + delimited_list(expression)("in") + RB)
                + RB
                + alias
            )("kwargs")
        ) / to_unpivot_call

        join = (
            pivot_join
            | unpivot_join
            | (
                Group(joins)("op")
                + table_source("join")
                + Optional((ON + expression("on")) | (USING + expression("using")))
                | (
                    Group(WINDOW)("op")
                    + Group(identifier("name") + AS + over_clause("value"))("join")
                )
            )
            / to_join_call
        )

        selection = (
            (
                (SELECT + "*" + EXCEPT.suppress())
                + (LB + delimited_list(select_column)("select_except") + RB)
            )
            | (SELECT + DISTINCT + ON)
            + (LB + delimited_list(select_column)("distinct_on") + RB)
            + delimited_list(select_column)("select")
            | SELECT + DISTINCT + delimited_list(select_column)("select_distinct")
            | (
                SELECT
                + Optional(
                    TOP
                    + expression("value")
                    + Optional(keyword("percent"))("percent")
                    + Optional(WITH + keyword("ties"))("ties")
                )("top")
                / to_top_clause
                + delimited_list(select_column)("select")
            )
        )

        row = (LB + delimited_list(Group(expression)) + RB) / to_row
        values = VALUES + delimited_list(row) / to_values

        unordered_sql = Group(
            values
            | selection
            + Optional(
                (FROM + delimited_list(table_source) + ZeroOrMore(join))("from")
                + Optional(WHERE + expression("where"))
                + Optional(GROUP_BY + delimited_list(Group(named_column))("groupby"))
                + Optional(HAVING + expression("having"))
                + Optional(QUALIFY + expression("qualify"))
            )
        )

        with NO_WHITESPACE:

            def mult(tokens):
                amount = tokens["bytes"]
                scale = tokens["scale"].lower()
                return {
                    "bytes": amount
                    * {"b": 1, "k": 1_000, "m": 1_000_000, "g": 1_000_000_000}[scale]
                }

            bytes_constraint = (
                (real_num | int_num)("bytes") + Char("bBkKmMgG")("scale")
            ) / mult

        # https://wiki.postgresql.org/wiki/TABLESAMPLE_Implementation
        # https://docs.snowflake.com/en/sql-reference/constructs/sample.html
        # https://docs.microsoft.com/en-us/sql/t-sql/queries/from-transact-sql?view=sql-server-ver16
        tablesample = (TABLESAMPLE | SAMPLE) + (
            Optional((
                keyword("bernoulli")
                | keyword("row")
                | keyword("system")
                | keyword("block")
            ))("method")
            # / (lambda t: t if t else "bernoulli")
            + LB
            + (
                (
                    keyword("bucket")("op")
                    + int_num("params")
                    + keyword("out of")
                    + int_num("params")
                    + Optional(ON + expression("on"))
                )
                / to_json_call
                | (real_num | int_num)("percent") + keyword("percent")
                | int_num("rows") + keyword("rows")
                | bytes_constraint
                | (real_num | int_num)("percent")
            )
            + RB
            + Optional(assign("repeatable", LB + int_num + RB))
        )("tablesample")

        unnest = (UNNEST("op") + LB + expression("params") + RB) / to_json_call
        lateral_source = (LATERAL("op") + table_source("params")) / to_json_call

        table_source << Group(
            (
                lateral_source
                | (LB + query + RB)
                | unnest
                | stack
                | call_function
                | identifier
            )("value")
            + MatchAll([
                Optional(flag("with ordinality")),
                Optional(WITH + LB + keyword("nolock")("hint") + RB),
                Optional(WITH + OFFSET + Optional(AS) + identifier("with_offset")),
                Optional(tablesample),
                alias,
            ])
        ) / to_table

        rows = Optional(keyword("row") | keyword("rows"))
        limit = (
            Optional(assign("offset", expression) + rows)
            & Optional(
                FETCH
                + Optional(keyword("first") | keyword("next"))
                + expression("fetch")
                + rows
                + Optional(keyword("only"))
            )
            & Optional(assign("limit", expression))
        )

        # https://www.postgresql.org/docs/current/sql-select.html
        #  [ FOR { UPDATE | NO KEY UPDATE | SHARE | KEY SHARE } [ OF table_name [, ...] ] [ NOWAIT | SKIP LOCKED ] [...] ]
        for_update = Optional(
            FOR
            + (keyword("update") | keyword("share") | keyword("no key update") | keyword("key share"))("mode")
            + Optional(
                keyword("of").suppress()
                + identifier("value")
                + Optional(flag("nowait") | flag("skip locked"))
            )("table")
        )("locking")

        ordered_sql = (
            (
                (unordered_sql | (LB + query + RB))
                + ZeroOrMore(
                    Group(
                        (UNION | INTERSECT | EXCEPT | MINUS) + Optional(ALL | DISTINCT)
                    )("op")
                    + (unordered_sql | (LB + query + RB))
                )
            )("union")
            + Optional(ORDER_BY + delimited_list(Group(sort_column))("orderby"))
            + limit
            + for_update
            + Optional(
                (UNION | INTERSECT | EXCEPT | MINUS) / bad_operator_on_ordered_sql
            )
        ) / to_union_call

        with_clause = delimited_list(Group(
            (
                (identifier("name") + Optional(LB + delimited_list(ident("col")) + RB))
                / to_alias
            )("name")
            + (AS + LB + (query | expression)("value") + RB)
        ))

        query << (
            Optional(
                assign("with recursive", with_clause) | assign("with", with_clause)
            )
            + Group(ordered_sql)("query")
        ) / to_query

        #####################################################################
        # DML STATEMENTS
        #####################################################################

        # MySQL's index_type := Using + ( "BTREE" | "HASH" )
        index_type = Optional(assign("using", ident("index_type")))

        index_column_names = LB + delimited_list(identifier("columns")) + RB

        column_def_delete = assign(
            "on delete",
            (keyword("cascade") | keyword("set null") | keyword("set default")),
        )

        table_def_foreign_key = FOREIGN_KEY + Optional(
            Optional(identifier("index_name"))
            + index_column_names
            + column_def_references
            + Optional(column_def_delete)
        )

        index_options = ZeroOrMore(identifier / (lambda t: {t[0]: True}))

        table_constraint_definition = Optional(CONSTRAINT + identifier("name")) + (
            assign("primary key", index_type + index_column_names + index_options)
            | (
                Optional(flag("unique"))
                + Optional(INDEX | KEY)
                + Optional(identifier("name"))
                + index_type
                + index_column_names
                + index_options
            )("index")
            | assign("check", LB + expression + RB)
            | table_def_foreign_key("foreign_key")
        )

        table_element = (
            column_definition("columns") | table_constraint_definition("constraint")
        )
        temporary = Optional(
            (
                Keyword("temporary", caseless=True) | Keyword("temp", caseless=True)
            )("temporary")
            / (lambda: True)
        ) + Optional(flag("transient"))

        create_table = (
            keyword("create")
            + Optional(keyword("or") + flag("replace"))
            + temporary
            + TABLE
            + Optional((keyword("if not exists") / (lambda: False))("replace"))
            + identifier("name")
            + Optional(LB + delimited_list(table_element) + RB)
            + ZeroOrMore(
                assign("engine", EQ + identifier)
                | assign("collate", EQ + identifier)
                | assign("auto_increment", EQ + int_num)
                | assign("comment", EQ + literal_string)
                | assign("default character set", EQ + identifier)
                | assign("default charset", EQ + identifier)
            )
            + Optional(AS.suppress() + infix_notation(query, [])("query"))
        )("create table")

        create_view = (
            keyword("create")
            + Optional(keyword("or") + flag("replace"))
            + temporary
            + VIEW.suppress()
            + Optional((keyword("if not exists") / (lambda: False))("replace"))
            + identifier("name")
            + AS
            + query("query")
        )("create view")

        # CREATE INDEX a ON u USING btree (e);
        create_index = (
            keyword("create index")
            + Optional(keyword("or") + flag("replace"))(INDEX | KEY)
            + Optional((keyword("if not exists") / (lambda: False))("replace"))
            + identifier("name")
            + ON
            + identifier("table")
            + index_type
            + index_column_names
            + index_options
        )("create index")

        cache_options = Optional((
            keyword("options").suppress()
            + LB
            + Dict(delimited_list(Group(
                literal_string / (lambda tokens: tokens[0]["literal"])
                + Optional(EQ)
                + identifier
            )))
            + RB
        )("options"))

        create_cache = (
            keyword("cache").suppress()
            + Optional(flag("lazy"))
            + TABLE
            + identifier("name")
            + cache_options
            + Optional(AS + query("query"))
        )("cache")

        drop_table = (
            keyword("drop table") + Optional(flag("if exists")) + identifier("table")
        )("drop")

        drop_view = (
            keyword("drop view") + Optional(flag("if exists")) + identifier("view")
        )("drop")

        drop_index = (
            keyword("drop index") + Optional(flag("if exists")) + identifier("index")
        )("drop")

        returning = Optional(delimited_list(select_column)("returning"))

        insert = (
            keyword("insert").suppress()
            + (
                flag("overwrite") + keyword("table").suppress()
                | keyword("into").suppress() + Optional(keyword("table").suppress())
            )
            + identifier("table")
            + Optional(LB + delimited_list(identifier)("columns") + RB)
            + Optional(flag("if exists"))
            + (values | query)("query")
            + returning
        ) / to_insert_call

        update = (
            keyword("update").suppress()
            + identifier("value")
            + Optional(identifier("name"))
            + assign("set", Dict(delimited_list(Group(identifier + EQ + expression))))
            + Optional((FROM + delimited_list(table_source) + ZeroOrMore(join))("from"))
            + Optional(WHERE + expression("where"))
            + returning
        ) / to_update_call

        delete = (
            keyword("delete")("op")
            + keyword("from").suppress()
            + identifier("params")
            + Optional(assign("where", expression))
            + returning
        ) / to_json_call

        #############################################################
        # PROCEDURAL
        #############################################################
        special_ident = (
            keyword("masking policy") | identifier / (lambda t: t[0].lower())
        )
        declare_variable = assign("declare", column_definition)
        set_variable = assign(
            "set",
            (special_ident + Optional(EQ) + expression)("params")
            / (lambda t: {
                t[0].lower(): t[1].lower() if isinstance(t[1], str) else t[1]
            }),
        )
        unset_variable = assign("unset", special_ident)

        copy_options = Forward()
        copy_options << ZeroOrMore(MatchFirst(
            [
                keyword(n).suppress()
                + EQ
                + (LB + copy_options + RB | expression)(n.lower())
                for n in copy_params
            ]
            + [PARTITION_BY.suppress() + expression("partition_by")]
        ))

        with NO_WHITESPACE:
            file_name = Regex("[a-zA-Z0-9-_!.]+")
            file_path = Optional(
                "/"
                + delimited_list(file_name, separator="/", combine=True)
                + Optional("/")
            )
            # @%load1/data1/
            file_source = Combine(
                Literal("@")
                + (
                    Literal("~") + file_path
                    | Literal("%") + file_name + file_path
                    | (
                        simple_ident
                        + Optional("." + Optional("%") + file_name)
                        + file_path
                    )
                )
                | (
                    CaselessLiteral("azure")
                    | CaselessLiteral("s3")
                    | CaselessLiteral("gcs")
                )
                + "://"
                + file_name
                + file_path
            )

        copy = assign(
            "copy",
            (
                assign("into", file_source | expression)
                + Optional(assign("from", file_source | expression))
                + copy_options
            ),
        )

        column_modifications = delimited_list(Group(
            Optional(Keyword("column", caseless=True).suppress())
            + identifier("name")
            + (
                keyword("set data type") + column_type
                | keyword("data type") + column_type
                | keyword("type") + column_type
                | set_variable
                | unset_variable
                | assign("drop", column_option | special_ident)
                | Optional(keyword("set")) + column_option
            )
        ))

        #############################################################
        # ALTER TABLE
        #############################################################

        alter = assign(
            "alter",
            (
                assign("table", identifier)
                + delimited_list(
                    assign("rename to", identifier)
                    | assign(
                        "rename",
                        assign("column", identifier("name") + TO + identifier("to")),
                    )
                    | assign("swap with", identifier)
                    | assign(
                        "add",
                        ZeroOrMore(
                            assign("column", column_definition)
                            | assign(
                                "constraint",
                                identifier("name") + ZeroOrMore(column_option),
                            )
                            | assign(
                                "row access policy",
                                identifier("policy")
                                + (ON + LB + delimited_list(identifier("on")) + RB),
                            )
                        ),
                    )
                    | assign(
                        "drop",
                        assign("column", identifier)
                        | assign("row access policy", identifier),
                    )
                    | (
                        (
                            Keyword("alter", caseless=True)
                            | Keyword("modify", caseless=True)
                        ).suppress()
                        + (LB + column_modifications + RB | column_modifications)
                    )("modify")
                    | assign("cluster by", LB + delimited_list(identifier) + RB)
                    #  MODIFY COLUMN empl_id UNSET MASKING POLICY
                )
            ),
        )

        set_parser_names()

        return (
            query
            | (insert | update | delete)
            | (create_table | create_view | create_cache | create_index)
            | (drop_table | drop_view | drop_index)
            | (copy | alter)
            | (
                Optional(keyword("alter session")).suppress()
                + (set_variable | unset_variable | declare_variable)
            )
        ).finalize()
