# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#


import subprocess
from urllib.parse import unquote

from pymysql import connect, cursors

from jx_mysql.utils import round_up_pow2
from jx_python import jx
from mo_dots import (
    coalesce,
    listwrap,
    unwrap,
    wrap,
    list_to_data,
    dict_to_data,
)
from mo_files import File, URL
from mo_future import transpose, utf8_json_encoder
from mo_http import http
from mo_json import *
from mo_kwargs import override
from mo_logs import Except, suppress_exception, strings
from mo_logs.strings import expand_template, indent, outdent
from mo_math import is_number
from mo_sql import *
from mo_times import Date, DAY
from pyLibrary import convert
from pyLibrary.meta import cache

DEBUG = True
MAX_BATCH_SIZE = 1
EXECUTE_TIMEOUT = (
    5 * 600 * 1000
)  # in milliseconds  SET TO ZERO (OR None) FOR HOST DEFAULT TIMEOUT

MYSQL_EXECUTABLE = "mysql"

all_db = []


class MySql(object):
    """
    Parameterize SQL by name rather than by position.  Return records as objects
    rather than tuples.
    """

    @override
    def __init__(
        self,
        host,  # CAN ALSO BE SET TO mysql://username:password@host:optional_port/database_name
        username=None,
        password=None,
        port=3306,
        debug=DEBUG,
        schema=None,
        db=None,  # ALIAS FOR schema
        preamble=None,
        readonly=False,
        kwargs=None,
    ):
        """
        OVERRIDE THE settings.schema WITH THE schema PARAMETER
        preamble WILL BE USED TO ADD COMMENTS TO THE BEGINNING OF ALL SQL
        THE INTENT IS TO HELP ADMINISTRATORS ID THE SQL RUNNING ON THE DATABASE

        schema - NAME OF DEFAULT database/schema IN QUERIES

        preamble - A COMMENT TO BE ADDED TO EVERY SQL STATEMENT SENT

        readonly - USED ONLY TO INDICATE IF A TRANSACTION WILL BE OPENED UPON
        USE IN with CLAUSE, YOU CAN STILL SEND UPDATES, BUT MUST OPEN A
        TRANSACTION BEFORE YOU DO
        """
        all_db.append(self)

        self.settings = kwargs
        self.query_cursor = None
        self.schema = coalesce(schema, db)
        if preamble is None:
            self.preamble = ""
        else:
            self.preamble = indent(preamble, "# ").strip() + "\n"

        self.readonly = readonly
        self.debug = debug or DEBUG
        if host:
            self._open()

    def _open(self):
        """ DO NOT USE THIS UNLESS YOU close() FIRST"""
        if self.settings.host.startswith("mysql://"):
            # DECODE THE URI: mysql://username:password@host:optional_port/database_name
            up = strings.between(self.settings.host, "mysql://", "@")
            if ":" in up:
                self.settings.username, self.settings.password = unquote(up).split(":")
            else:
                self.settings.username = up

            url = strings.between(self.settings.host, "@", None)
            hp, self.settings.schema = url.split("/", 1)
            if ":" in hp:
                self.settings.host, self.settings.port = hp.split(":")
                self.settings.port = int(self.settings.port)
            else:
                self.settings.host = hp

        # SSL PEM
        if self.settings.host in ("localhost", "mysql", "127.0.0.1"):
            ssl_context = None
        else:
            if self.settings.ssl and not self.settings.ssl.pem:
                Log.error("Expecting 'pem' property in ssl")
            # ssl_context = ssl.create_default_context(**get_ssl_pem_file(self.settings.ssl.pem))
            filename = File(".pem") / URL(self.settings.ssl.pem).host
            filename.write_bytes(http.get(self.settings.ssl.pem).content)
            ssl_context = {"ca": filename.abspath}

        try:
            self.db = connect(
                host=self.settings.host,
                port=self.settings.port,
                user=coalesce(self.settings.username, self.settings.user),
                passwd=coalesce(self.settings.password, self.settings.passwd),
                read_timeout=coalesce(
                    self.settings.read_timeout,
                    (EXECUTE_TIMEOUT / 1000) - 10 if EXECUTE_TIMEOUT else None,
                    5 * 60,
                ),
                charset="utf8",
                use_unicode=True,
                ssl=ssl_context,
                cursorclass=cursors.SSCursor,
            )
        except Exception as e:
            if "://" not in self.settings.host:
                Log.error(
                    "Failure to connect to {{host}}:{{port}}",
                    host=self.settings.host,
                    port=self.settings.port,
                    cause=e,
                )
            else:
                Log.error("Failure to connect.  PROTOCOL PREFIX IS PROBABLY BAD", e)
        self.partial_rollback = False
        self.transaction_level = 0
        self.backlog = []  # accumulate the write commands so they are sent at once

    def __enter__(self):
        if not self.readonly:
            self.begin()
        return self

    def __exit__(self, type, value, traceback):
        if self.readonly:
            self.close()
            return

        if isinstance(value, BaseException):
            try:
                if self.transaction_level:
                    self.rollback()
            except Exception as e:
                Log.warning("can not rollback()", cause=[value, e])
            finally:
                self.close()
            return

        try:
            self.commit()
        except Exception as e:
            Log.warning("can not commit()", e)
        finally:
            self.close()

    def transaction(self):
        """
        return not-started transaction (for with statement)
        """
        return Transaction(self)

    def begin(self):
        self.transaction_level += 1
        if self.schema:
            self.execute(str("USE" + quote_column(self.schema)))
        self.execute("SET TIME_ZONE='+00:00'")
        if EXECUTE_TIMEOUT:
            try:
                self.execute("SET MAX_EXECUTION_TIME=" + text(EXECUTE_TIMEOUT))
                self._execute_backlog()
            except Exception as e:
                e = Except.wrap(e)
                if "Unknown system variable 'MAX_EXECUTION_TIME'" in e:
                    globals()["EXECUTE_TIMEOUT"] = (
                        0  # THIS VERSION OF MYSQL DOES NOT HAVE SESSION LEVEL VARIABLE
                    )
                else:
                    raise e

    def close(self):
        if self.transaction_level > 0:
            if self.readonly:
                self.commit()  # AUTO-COMMIT
            else:
                Log.error("expecting commit() or rollback() before close")
        try:
            self.db.close()
        except Exception as e:
            e = Except.wrap(e)
            if "Already closed" in e:
                return

            Log.warning("can not close()", e)
        finally:
            try:
                all_db.remove(self)
            except Exception as e:
                Log.error("not expected", cause=e)

    def commit(self):
        try:
            self._execute_backlog()
        except Exception as e:
            with suppress_exception:
                self.rollback()
            Log.error("Error while processing backlog", e)

        if self.transaction_level == 0:
            Log.error("No transaction has begun")
        elif self.transaction_level == 1:
            if self.partial_rollback:
                with suppress_exception:
                    self.rollback()

                Log.error("Commit after nested rollback is not allowed")
            else:
                self.db.commit()

        self.transaction_level -= 1

    def flush(self):
        try:
            self.commit()
        except Exception as e:
            Log.error("Can not flush", e)

        try:
            self.begin()
        except Exception as e:
            Log.error("Can not flush", e)

    def rollback(self):
        self.backlog = []  # YAY! FREE!
        if self.transaction_level == 0:
            Log.error("No transaction has begun")
        elif self.transaction_level == 1:
            self.transaction_level -= 1
            self.db.rollback()
        else:
            self.transaction_level -= 1
            self.partial_rollback = True
            Log.warning("Can not perform partial rollback!")

    def call(self, proc_name, params):
        self._execute_backlog()
        params = [unwrap(v) for v in params]
        try:
            with self.db.cursor() as cursor:
                cursor.callproc(proc_name, params)
        except Exception as e:
            Log.error("Problem calling procedure " + proc_name, e)

    def query(self, sql, param=None, stream=False, format=None):
        """
        RETURN A LIST OF dicts

        :param sql:  SQL TEMPLATE TO SEND
        :param param: PARAMETERS TO INJECT INTO SQL TEMPLATE
        :param stream: STREAM OUTPUT
        :param row_tuples: DO NOT RETURN dicts
        """
        if not self.transaction_level and self.backlog:
            Log.error("must perform all queries inside a transaction")
        self._execute_backlog()

        try:
            if isinstance(sql, SQL):
                sql = str(sql)
            if param:
                sql = expand_template(sql, quote_param(param))
            sql = self.preamble + outdent(sql)
            self.debug and Log.note(
                "Execute SQL:\n{{sql}}", sql=indent(sql), stack_depth=1
            )

            if not stream:
                with self.db.cursor() as cursor:
                    cursor.execute(sql)

                    columns = tuple(
                        utf8_to_unicode(d[0]) for d in coalesce(cursor.description, [])
                    )

                    if format == "table":
                        return dict_to_data({"header": columns, "data": list(cursor)})
                    elif format == "list":
                        return [dict(zip(columns, row)) for row in cursor]
                    else:
                        # original bugzilla etl (names are dot-delimited paths)
                        return [
                            leaves_to_data(dict(zip(columns, row))) for row in cursor
                        ]

            Log.error("not tested")

            cursor = self.db.cursor().__enter__()
            cursor.execute(sql)

            columns = tuple(
                utf8_to_unicode(d[0]) for d in coalesce(cursor.description, [])
            )

            if format == "list":
                # SIMPLE RETURN
                def tuple_streamer():
                    try:
                        yield from cursor
                    finally:
                        cursor.__exit__()

                return {"header": columns, "data": tuple_streamer}

            def streamer():
                try:
                    for row in cursor:
                        yield leaves_to_data(dict(zip(columns, row)))
                finally:
                    cursor.__exit__()

            return streamer()

        except Exception as e:
            e = Except.wrap(e)
            if "InterfaceError" in e:
                Log.error("Did you close the db connection?", e)
            Log.error(
                "Problem executing SQL:\n{{sql|indent}}",
                sql=sql,
                cause=e,
                stack_depth=1,
            )

    def column_query(self, sql, param=None):
        """
        RETURN RESULTS IN [column][row_num] GRID
        """
        self._execute_backlog()
        try:
            with self.db.cursor() as cursor:
                cursor.execute("SET TIME_ZONE='+00:00'")

            if param:
                sql = expand_template(sql, quote_param(param))
            sql = self.preamble + outdent(sql)
            self.debug and Log.note("Execute SQL:\n{{sql}}", sql=indent(sql))

            with self.db.cursor() as cursor:
                cursor.execute(sql)
                grid = [[utf8_to_unicode(c) for c in row] for row in cursor]
                # columns = [utf8_to_unicode(d[0]) for d in coalesce(cursor.description, [])]
            result = transpose(*grid)

            return result
        except Exception as e:
            e = Except.wrap(e)
            if "InterfaceError" in e:
                Log.error("Did you close the db connection?", e)
            Log.error(
                "Problem executing SQL:\n{{sql|indent}}",
                sql=sql,
                cause=e,
                stack_depth=1,
            )

    # EXECUTE GIVEN METHOD FOR ALL ROWS RETURNED
    def forall(self, sql, param=None, _execute=None):
        assert _execute
        num = 0

        self._execute_backlog()
        try:
            if param:
                sql = expand_template(sql, quote_param(param))
            sql = self.preamble + outdent(sql)
            self.debug and Log.note("Execute SQL:\n{{sql}}", sql=indent(sql))
            with self.db.cursor() as cursor:
                cursor.execute(sql)
                columns = tuple([
                    utf8_to_unicode(d[0].lower()) for d in cursor.description
                ])
                for r in cursor:
                    num += 1
                    _execute(wrap(dict(zip(columns, [utf8_to_unicode(c) for c in r]))))

        except Exception as e:
            Log.error(
                "Problem executing SQL:\n{{sql|indent}}",
                sql=sql,
                cause=e,
                stack_depth=1,
            )

        return num

    def execute(self, sql, param=None):
        if self.transaction_level == 0:
            Log.error("Expecting transaction to be started before issuing queries")

        if param:
            sql = expand_template(text(sql), quote_param(param))
        sql = outdent(str(sql))
        self.backlog.append(sql)
        if self.debug or len(self.backlog) >= MAX_BATCH_SIZE:
            self._execute_backlog()

    def _execute_backlog(self):
        if not self.backlog:
            return

        backlog, self.backlog = self.backlog, []
        for i, g in jx.chunk(backlog, size=MAX_BATCH_SIZE):
            sql = self.preamble + ";\n".join(g)
            try:
                self.debug and Log.note(
                    "Execute block of SQL:\n{{sql|indent}}", sql=sql
                )
                with self.db.cursor() as cursor:
                    cursor.execute(sql)
            except Exception as e:
                Log.error(
                    "Problem executing SQL:\n{{sql|indent}}",
                    sql=sql,
                    cause=e,
                    stack_depth=1,
                )

    ## Insert dictionary of values into table
    def insert(self, table_name, record):
        keys = list(record.keys())

        try:
            command = (
                SQL_INSERT
                + quote_column(table_name)
                + sql_iso(sql_list([quote_column(k) for k in keys]))
                + SQL_VALUES
                + sql_iso(sql_list([quote_value(record[k]) for k in keys]))
            )
            self.execute(command)
        except Exception as e:
            Log.error("problem with record: {{record}}", record=record, cause=e)

    # candidate_key IS LIST OF COLUMNS THAT CAN BE USED AS UID (USUALLY PRIMARY KEY)
    # ONLY INSERT IF THE candidate_key DOES NOT EXIST YET
    def insert_new(self, table_name, candidate_key, new_record):
        candidate_key = listwrap(candidate_key)

        condition = sql_eq(**{k: new_record[k] for k in candidate_key})
        command = (
            SQL_INSERT
            + quote_column(table_name)
            + sql_iso(sql_list(quote_column(k) for k in new_record.keys()))
            + SQL_SELECT
            + "a.*"
            + SQL_FROM
            + sql_iso(
                SQL_SELECT
                + sql_list([
                    quote_value(v) + " " + quote_column(k)
                    for k, v in new_record.items()
                ])
                + SQL_FROM
                + "DUAL"
            )
            + " a"
            + SQL_LEFT_JOIN
            + sql_iso(
                SQL_SELECT
                + "'dummy' exist "
                + SQL_FROM
                + quote_column(table_name)
                + SQL_WHERE
                + condition
                + SQL_LIMIT
                + SQL_ONE
            )
            + " b ON "
            + SQL_TRUE
            + SQL_WHERE
            + " exist "
            + SQL_IS_NULL
        )
        self.execute(command, {})

    # ONLY INSERT IF THE candidate_key DOES NOT EXIST YET
    def insert_newlist(self, table_name, candidate_key, new_records):
        for r in new_records:
            self.insert_new(table_name, candidate_key, r)

    def insert_list(self, table_name, records):
        if not records:
            return

        keys = set()
        for r in records:
            keys |= set(r.keys())
        keys = jx.sort(keys)

        try:
            command = (
                SQL_INSERT
                + quote_column(table_name)
                + sql_iso(sql_list([quote_column(k) for k in keys]))
                + SQL_VALUES
                + sql_list(
                    sql_iso(sql_list([quote_value(r[k]) for k in keys]))
                    for r in records
                )
            )
            self.execute(command)
        except Exception as e:
            Log.error("problem with record: {{record}}", record=records, cause=e)

    def update(self, table_name, where_slice, new_values):
        """
        where_slice - A Data WHICH WILL BE USED TO MATCH ALL IN table
                      eg {"id": 42}
        new_values  - A dict WITH COLUMN NAME, COLUMN VALUE PAIRS TO SET
        """
        new_values = quote_param(new_values)

        where_clause = sql_eq(**where_slice)

        command = (
            SQL_UPDATE
            + quote_column(table_name)
            + SQL_SET
            + sql_list([quote_column(k) + "=" + v for k, v in new_values.items()])
            + SQL_WHERE
            + where_clause
        )
        self.execute(command, {})

    def sort2sqlorderby(self, sort):
        sort = jx.normalize_sort_parameters(sort)
        return sql_list([
            quote_column(s.field) + (SQL_DESC if s.sort == -1 else SQL_ASC)
            for s in sort
        ])

    def about(self, table_name):
        try:
            with self.transaction() as t:
                return t.query("DESC" + quote_column(table_name))
        except Exception as cause:
            return None

    def get_tables(self):
        result = self.query(str(sql_query({
            "from": "information_schema.tables",
            "where": {"eq": {"table_schema": self.schema}},
            "orderby": "table_name",
        })))
        return list_to_data([{"name": d.TABLE_NAME} for d in result])

    def get_relations(self, table):
        raw_relations = self.query(
            """
            SELECT
                table_schema,
                table_name,
                referenced_table_schema,
                referenced_table_name,
                referenced_column_name,
                constraint_name,
                column_name,
                ordinal_position
            FROM
                information_schema.key_column_usage
            WHERE
                referenced_column_name IS NOT NULL
            """
        )
        if raw_relations:
            raise NotImplementedError()
        return raw_relations


@override
def execute_sql(host, username, password, sql, schema=None, param=None, kwargs=None):
    """EXECUTE MANY LINES OF SQL (FROM SQLDUMP FILE, MAYBE?"""
    kwargs.schema = coalesce(kwargs.schema, kwargs.database)

    if param:
        with MySql(kwargs) as temp:
            sql = expand_template(sql, quote_param(param))

    # We have no way to execute an entire SQL file in bulk, so we
    # have to shell out to the commandline client.
    args = [
        MYSQL_EXECUTABLE,
        "-h{0}".format(host),
        "-u{0}".format(username),
        "-p{0}".format(password),
    ]
    if schema:
        args.append("{0}".format(schema))

    try:
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=-1,
        )
        if is_text(sql):
            sql = sql.encode("utf8")
        (output, _) = proc.communicate(sql)
    except Exception as e:
        raise Log.error('Can not call "mysql"', e)

    if proc.returncode:
        if len(sql) > 10000:
            sql = "<" + text(len(sql)) + " bytes of sql>"
        Log.error(
            "Unable to execute sql: return code {{return_code}}, {{output}}:\n"
            " {{sql}}\n",
            sql=indent(sql),
            return_code=proc.returncode,
            output=output,
        )


@override
def execute_file(
    filename,
    host,
    username,
    password,
    schema=None,
    param=None,
    ignore_errors=False,
    kwargs=None,
):
    # MySqldb provides no way to execute an entire SQL file in bulk, so we
    # have to shell out to the commandline client.
    file = File(filename)
    if file.extension == "zip":
        sql = file.read_zipfile()
    else:
        sql = File(filename).read()

    if ignore_errors:
        with suppress_exception:
            execute_sql(sql=sql, kwargs=kwargs)
    else:
        execute_sql(sql=sql, kwargs=kwargs)


ESCAPE_DCT = {
    "\\": "\\\\",
    "\0": "\\0",
    '"': '\\"',
    "'": "''",
    "\b": "\\b",
    "\f": "\\f",
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def quote_value(value):
    """
    convert values to mysql code for the same
    mostly delegate directly to the mysql lib, but some exceptions exist
    """
    try:
        if value == None:
            return SQL_NULL
        elif value is True:
            return SQL_TRUE
        elif value is False:
            return SQL_FALSE
        elif isinstance(value, SQL):
            return value
        elif isinstance(value, Date):
            return SQL(text(value.unix))
        elif isinstance(value, Duration):
            return SQL(text(value.seconds))
        elif is_text(value):
            return SQL("'" + "".join(ESCAPE_DCT.get(c, c) for c in value) + "'")
        elif is_data(value):
            return quote_value(json_encode(value))
        elif isinstance(value, datetime):
            return SQL(
                "str_to_date('"
                + value.strftime("%Y%m%d%H%M%S.%f")
                + "', '%Y%m%d%H%i%s.%f')"
            )
        elif isinstance(value, Date):
            return SQL(
                "str_to_date('"
                + value.format("%Y%m%d%H%M%S.%f")
                + "', '%Y%m%d%H%i%s.%f')"
            )
        elif is_number(value):
            return SQL(text(value))
        elif hasattr(value, "__iter__"):
            return quote_value(json_encode(value))
        else:
            return quote_value(text(value))
    except Exception as e:
        Log.error("problem quoting SQL {{value}}", value=repr(value), cause=e)


def quote_column(*path):
    if DEBUG:
        if not path:
            Log.error("expecting a name")
        for p in path:
            if not is_text(p):
                Log.error("expecting strings, not {{type}}", type=p.__class__.__name__)
    try:
        output = ConcatSQL(
            SQL_SPACE,
            JoinSQL(SQL_DOT, [SQL(_simple_quote_column(p)) for p in path]),
            SQL_SPACE,
        )
        return output
    except Exception as e:
        Log.error("Not expacted", cause=e)


def quote_sql(value, param=None):
    """
    USED TO EXPAND THE PARAMETERS TO THE SQL() OBJECT
    """
    try:
        if isinstance(value, SQL):
            if not param:
                return value
            param = {k: quote_sql(v) for k, v in param.items()}
            return SQL(expand_template(value, param))
        elif is_text(value):
            return SQL(value)
        elif is_data(value):
            return quote_value(json_encode(value))
        elif hasattr(value, "__iter__"):
            return quote_list(value)
        else:
            return text(value)
    except Exception as e:
        Log.error("problem quoting SQL", e)


def sql_alias(value, alias):
    if not isinstance(value, SQL) or not is_text(alias):
        Log.error("Expecting (SQL, text) parameters")
    return ConcatSQL(value, SQL_AS, quote_column(alias))


def quote_param(param):
    return {k: quote_value(v) for k, v in param.items()}


def quote_list(values):
    return sql_iso(sql_list(map(quote_value, values)))


def sql_call(func_name, parameters):
    return ConcatSQL(SQL(func_name), sql_iso(JoinSQL(SQL_COMMA, parameters)))


def sql_eq(**item):
    """
    RETURN SQL FOR COMPARING VARIABLES TO VALUES (AND'ED TOGETHER)

    :param item: keyword parameters representing variable and value
    :return: SQL
    """

    return SQL_AND.join([
        ConcatSQL(quote_column(k), SQL_EQ, quote_value(v))
        if v != None
        else ConcatSQL(quote_column(k), SQL_IS_NULL)
        for k, v in item.items()
    ])


def sql_query(command):
    """
    VERY BASIC QUERY EXPRESSION TO SQL
    :param command: jx-expression
    :return: SQL
    """
    command = wrap(command)
    acc = [SQL_SELECT]
    if command.select:
        acc.append(JoinSQL(SQL_COMMA, map(quote_column, listwrap(command.select))))
    else:
        acc.append(SQL_STAR)

    acc.append(SQL_FROM)
    acc.append(quote_column(*split_field(command["from"])))
    if command.where:
        acc.append(SQL_WHERE)
        if command.where.eq:
            acc.append(sql_eq(**command.where.eq))
        else:
            where = esfilter2sqlwhere(command.where)
            acc.append(where)

    sort = coalesce(command.orderby, command.sort)
    if sort:
        acc.append(SQL_ORDERBY)
        acc.append(JoinSQL(SQL_COMMA, map(quote_column, listwrap(sort))))

    if command.limit:
        acc.append(SQL_LIMIT)
        acc.append(JoinSQL(SQL_COMMA, map(quote_value, listwrap(command.limit))))

    return ConcatSQL(*acc)


def utf8_to_unicode(v):
    try:
        if is_binary(v):
            return v.decode("utf8")
        else:
            return v
    except Exception as e:
        Log.error("not expected", e)


def int_list_packer(term, values):
    """
    return singletons, ranges and exclusions
    """
    DENSITY = 10  # a range can have holes, this is inverse of the hole density
    MIN_RANGE = 20  # min members before a range is allowed to be used

    singletons = set()
    ranges = []
    exclude = set()

    sorted = jx.sort(values)

    last = sorted[0]
    curr_start = last
    curr_excl = set()

    for v in sorted[1::]:
        if v <= last + 1:
            pass
        elif v - last > 3:
            # big step, how do we deal with it?
            if last == curr_start:
                # not a range yet, so just add as singlton
                singletons.add(last)
            elif last - curr_start - len(curr_excl) < MIN_RANGE or (
                (last - curr_start) < len(curr_excl) * DENSITY
            ):
                # small ranges are singletons, sparse ranges are singletons
                singletons |= set(range(curr_start, last + 1))
                singletons -= curr_excl
            else:
                # big enough, and dense enough range
                ranges.append({"gte": curr_start, "lte": last})
                exclude |= curr_excl
            curr_start = v
            curr_excl = set()
        else:
            if 1 + last - curr_start >= len(curr_excl) * DENSITY:
                # high density, keep track of excluded and continue
                add_me = set(range(last + 1, v))
                curr_excl |= add_me
            elif 1 + last - curr_start - len(curr_excl) < MIN_RANGE:
                # not big enough, convert range to singletons
                new_singles = set(range(curr_start, last + 1)) - curr_excl
                singletons = singletons | new_singles

                curr_start = v
                curr_excl = set()
            else:
                ranges.append({"gte": curr_start, "lte": last})
                exclude |= curr_excl
                curr_start = v
                curr_excl = set()
        last = v

    if last == curr_start:
        # not a range yet, so just add as singlton
        singletons.add(last)
    elif last - curr_start - len(curr_excl) < MIN_RANGE or (
        (last - curr_start) < len(curr_excl) * DENSITY
    ):
        # small ranges are singletons, sparse ranges are singletons
        singletons |= set(range(curr_start, last + 1))
        singletons -= curr_excl
    else:
        # big enough, and dense enough range
        ranges.append({"gte": curr_start, "lte": last})
        exclude |= curr_excl

    if ranges:
        r = {"or": [{"range": {term: r}} for r in ranges]}
        if exclude:
            r = {"and": [r, {"not": {"terms": {term: jx.sort(exclude)}}}]}
        if singletons:
            return {"or": [{"terms": {term: jx.sort(singletons)}}, r]}
        else:
            return r
    else:
        return {"terms": {term: values}}


class Transaction(object):
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        self.db.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_val, Exception):
            self.db.rollback()
        else:
            self.db.commit()

    def execute(self, command, **param):
        self.db.execute(command, **param)

    def query(self, query, **param):
        return self.db.query(query, **param)


def json_encode(value):
    """
    FOR PUTTING JSON INTO DATABASE (sort_keys=True)
    dicts CAN BE USED AS KEYS
    """
    return text(utf8_json_encoder(scrub(value)))


def esfilter2sqlwhere(esfilter):
    return _esfilter2sqlwhere(esfilter)


def _esfilter2sqlwhere(esfilter):
    """
    CONVERT ElassticSearch FILTER TO SQL FILTER
    db - REQUIRED TO PROPERLY QUOTE VALUES AND COLUMN NAMES
    """
    esfilter = wrap(esfilter)

    if esfilter is True:
        return SQL_TRUE
    elif esfilter["and"]:
        return sql_iso(SQL_AND.join([esfilter2sqlwhere(a) for a in esfilter["and"]]))
    elif esfilter["or"]:
        return sql_iso(SQL_OR.join([esfilter2sqlwhere(a) for a in esfilter["or"]]))
    elif esfilter["not"]:
        return SQL_NOT + sql_iso(esfilter2sqlwhere(esfilter["not"]))
    elif esfilter.term:
        return sql_iso(SQL_AND.join([
            quote_column(col) + SQL("=") + quote_value(val)
            for col, val in esfilter.term.items()
        ]))
    elif esfilter.eq:
        col, val = first(esfilter.eq.items())
        return ConcatSQL(quote_column(col), SQL_EQ, quote_value(val))
    elif esfilter.terms:
        for col, v in esfilter.terms.items():
            if len(v) == 0:
                return "FALSE"

            try:
                int_list = convert.value2intlist(v)
                has_null = any(vv == None for vv in v)
                if int_list:
                    filter = int_list_packer(col, int_list)
                    if has_null:
                        return esfilter2sqlwhere({"or": [{"missing": col}, filter]})
                    elif "terms" in filter and set(filter["terms"].get(
                        col, []
                    )) == set(int_list):
                        return quote_column(col) + " in " + quote_list(int_list)
                    else:
                        return esfilter2sqlwhere(filter)
                else:
                    if has_null:
                        return esfilter2sqlwhere({"missing": col})
                    else:
                        return "false"
            except Exception as e:
                e = Except.wrap(e)
                pass
            return quote_column(col) + " in " + quote_list(v)
    elif esfilter.script:
        return sql_iso(esfilter.script)
    elif esfilter.gt:
        k, v = first(esfilter.gt.items())
        return ConcatSQL(quote_column(k), SQL_GT, quote_value(v))
    elif esfilter.range:
        name2sign = {"gt": SQL(">"), "gte": SQL(">="), "lte": SQL("<="), "lt": SQL("<")}

        def single(col, r):
            min = coalesce(r["gte"], r[">="])
            max = coalesce(r["lte"], r["<="])
            if min != None and max != None:
                # SPECIAL CASE (BETWEEN)
                sql = (
                    quote_column(col)
                    + SQL(" BETWEEN ")
                    + quote_value(min)
                    + SQL_AND
                    + quote_value(max)
                )
            else:
                sql = SQL_AND.join(
                    quote_column(col) + name2sign[sign] + quote_value(value)
                    for sign, value in r.items()
                )
            return sql

        terms = [single(col, ranges) for col, ranges in esfilter.range.items()]
        if len(terms) == 1:
            output = terms[0]
        else:
            output = sql_iso(SQL_AND.join(terms))
        return output
    elif esfilter.missing:
        if isinstance(esfilter.missing, text):
            return sql_iso(quote_column(esfilter.missing) + SQL_IS_NULL)
        else:
            return sql_iso(quote_column(esfilter.missing.field) + SQL_IS_NULL)
    elif esfilter.exists:
        if isinstance(esfilter.exists, text):
            return sql_iso(quote_column(esfilter.exists) + SQL_IS_NOT_NULL)
        else:
            return sql_iso(quote_column(esfilter.exists.field) + SQL_IS_NOT_NULL)
    elif esfilter.match_all:
        return SQL_TRUE
    elif esfilter.instr:
        return sql_iso(SQL_AND.join([
            "instr" + sql_iso(quote_column(col) + ", " + quote_value(val)) + ">0"
            for col, val in esfilter.instr.items()
        ]))
    else:
        Log.error("Can not convert esfilter to SQL: {{esfilter}}", esfilter=esfilter)


_mysql_type_to_json_type = {
    "bigint": INTEGER,
    "blob": STRING,
    "char": STRING,
    "datetime": TIME,
    "decimal": NUMBER,
    "double": NUMBER,
    "enum": INTEGER,
    "float": NUMBER,
    "int": INTEGER,
    "longblob": STRING,
    "longtext": STRING,
    "mediumblob": STRING,
    "mediumint": INTEGER,
    "mediumtext": STRING,
    "set": "array",
    "smallint": INTEGER,
    "text": STRING,
    "time": INTERVAL,
    "timestamp": TIME,
    "tinyint": INTEGER,
    "tinytext": STRING,
    "varchar": STRING,
}


def mysql_type_to_json_type(mysql_type):
    if "(" in mysql_type:
        simple_type, size = mysql_type.split("(")
    else:
        simple_type = mysql_type

    return _mysql_type_to_json_type[simple_type]


_json_type_to_mysql_type = {
    INTEGER: "bigint",
    STRING: "varchar",
    TIME: "datetime",
    NUMBER: "double",
    INTERVAL: "timestamp",
}


def json_type_to_mysql_type(json_type, value):
    mysql_type = _json_type_to_mysql_type.get(json_type)
    if json_type == STRING:
        length = min(16, round_up_pow2(len(value)))
        mysql_type = mysql_type + f"({length})"
    return mysql_type


def get_es_type_length(es_type):
    return int(strings.between(es_type, "(", ")"))


@cache(duration=DAY)
def get_ssl_pem_file(url):
    filename = File(".pem") / URL(url).host
    filename.write_bytes(http.get(url).content)
    return {"cafile": filename.abspath}


_simple_word = re.compile(r"^[_a-zA-Z][_0-9a-zA-Z]*$", re.UNICODE)


def _simple_quote_column(name):
    if _simple_word.match(name):
        return name
    name = name.replace("`", "``")
    return f"`{name}`"


def sql_eq(**item):
    """
    RETURN SQL FOR COMPARING VARIABLES TO VALUES (AND'ED TOGETHER)

    :param item: keyword parameters representing variable and value
    :return: SQL
    """
    return SQL_AND.join([
        ConcatSQL(quote_column(text(k)), SQL_EQ, quote_value(v))
        if v != None
        else ConcatSQL(quote_column(text(k)), SQL_IS_NULL)
        for k, v in item.items()
    ])


def sql_lt(**item):
    """
    RETURN SQL FOR LESS-THAN (<) COMPARISION BETWEEN VARIABLES TO VALUES

    :param item: keyword parameters representing variable and value
    :return: SQL
    """
    k, v = first(item.items())
    return ConcatSQL(quote_column(k), SQL_LT, quote_value(v))


def sql_create(table, properties, primary_key=None, unique=None):
    """
    :param table:  NAME OF THE TABLE TO CREATE
    :param properties: DICT WITH {name: type} PAIRS (type can be plain text)
    :param primary_key: COLUMNS THAT MAKE UP THE PRIMARY KEY
    :param unique: COLUMNS THAT SHOULD BE UNIQUE
    :return:
    """
    acc = [
        SQL_CREATE,
        quote_column(table),
        SQL_OP,
        sql_list([quote_column(k) + SQL(v) for k, v in properties.items()]),
    ]
    primary_key = listwrap(primary_key)

    if primary_key:
        acc.append(SQL_COMMA),
        acc.append(SQL(" PRIMARY KEY ")),
        acc.append(sql_iso(sql_list([quote_column(c) for c in listwrap(primary_key)])))
    if unique:
        acc.append(SQL_COMMA),
        acc.append(SQL(" UNIQUE ")),
        acc.append(sql_iso(sql_list([quote_column(c) for c in listwrap(unique)])))

    acc.append(SQL_CP)
    if primary_key and not (
        len(primary_key) == 1 and properties[primary_key[0]] == "INTEGER"
    ):
        acc.append(SQL(" WITHOUT ROWID"))
    return ConcatSQL(*acc)


def sql_insert(table, records):
    records = listwrap(records)
    keys = list({k for r in records for k in r.keys()})
    return ConcatSQL(
        SQL_INSERT,
        quote_column(table),
        sql_iso(sql_list(map(quote_column, keys))),
        SQL_VALUES,
        sql_list(sql_iso(sql_list([quote_value(r[k]) for k in keys])) for r in records),
    )


BEGIN = "BEGIN"
COMMIT = "COMMIT"
ROLLBACK = "ROLLBACK"
