# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#

from __future__ import absolute_import, division, unicode_literals

from mo_future import is_text, first
from mo_logs import Log

ENABLE_TYPE_CHECKING = True


class SQL(object):
    """
    THIS CLASS USES THE TYPE SYSTEM TO PREVENT SQL INJECTION ATTACKS
    ENSURES ONLY SQL OBJECTS ARE CONCATENATED TO MAKE MORE SQL OBJECTS
    """

    __slots__ = []

    def __new__(cls, value=None, *args, **kwargs):
        if not args and is_text(value):
            return object.__new__(TextSQL)
        else:
            return object.__new__(cls)

    @property
    def sql(self):
        return "".join(self)

    def __iter__(self):
        raise Log.error("not implemented")

    def __len__(self):
        return len(self.sql)

    def __add__(self, other):
        if not isinstance(other, SQL):
            if (
                is_text(other)
                and ENABLE_TYPE_CHECKING
                and all(c not in other for c in ('"', "'", "`", "\\"))
            ):
                return ConcatSQL(self, SQL(other))
            Log.error("Can only concat other SQL")
        else:
            return ConcatSQL(self, other)

    def __radd__(self, other):
        if not isinstance(other, SQL):
            if (
                is_text(other)
                and ENABLE_TYPE_CHECKING
                and all(c not in other for c in ('"', "'", "`", "\\"))
            ):
                return ConcatSQL(SQL(other), self)
            Log.error("Can only concat other SQL", stack_depth=1)
        else:
            return ConcatSQL(other, self)

    def join(self, list_):
        return JoinSQL(self, list_)

    def __data__(self):
        return self.sql

    def __str__(self):
        return "".join(self)


class TextSQL(SQL):
    __slots__ = ["value"]

    def __init__(self, value):
        """
        ACTUAL SQL, DO NOT QUOTE value
        """
        SQL.__init__(self)
        if ENABLE_TYPE_CHECKING and isinstance(value, SQL):
            Log.error("Expecting text, not SQL")
        self.value = value

    def __iter__(self):
        yield self.value


class JoinSQL(SQL):
    __slots__ = ["sep", "concat"]

    def __init__(self, sep, concat):
        """
        CONVIENENCE METHOD TO str.join() SOME SQL
        :param sep: THE SEPARATOR
        :param concat:  A LIST/TUPLE/ITERABLE OF SQL
        """
        SQL.__init__(self)
        if ENABLE_TYPE_CHECKING:
            if not isinstance(concat, (tuple, list)):
                concat = tuple(concat)
            if not isinstance(sep, SQL):
                Log.error("Expecting SQL, not text")
            if any(not isinstance(s, SQL) for s in concat):
                Log.error("Can only join other SQL")
        self.sep = sep
        self.concat = concat

    def __iter__(self):
        sep = NO_SQL
        for v in self.concat:
            yield from sep
            sep = self.sep
            yield from v


class IndentSQL(SQL):
    __slots__ = ["concat"]

    def __init__(self, concat):
        SQL.__init__(self)
        if ENABLE_TYPE_CHECKING:
            if not isinstance(concat, (tuple, list)):
                concat = tuple(concat)
            if any(not isinstance(s, SQL) for s in concat):
                Log.error("Can only join other SQL")
        self.concat = concat

    def __iter__(self):
        new_line = True
        for v in self.concat:
            for vv in v:
                if new_line:
                    yield from SQL_INDENT
                    new_line = False
                yield vv
                if vv == "\n":
                    new_line = True


class ConcatSQL(SQL):
    __slots__ = ["concat"]

    def __init__(self, *concat):
        """
        A SEQUENCE OF SQL FOR EVENTUAL CONCATENATION
        """
        if ENABLE_TYPE_CHECKING:
            if any(not isinstance(s, SQL) for s in concat):
                Log.error("Can only join other SQL not {value}", value=first(s for s in concat if not isinstance(s, SQL)))
        self.concat = concat

    def __iter__(self):
        for c in self.concat:
            yield from c


SQL_SPACE = SQL(" ")
SQL_CR = SQL("\n")
SQL_INDENT = SQL("   ")

NO_SQL = tuple()
SQL_STAR = SQL(" * ")
SQL_PLUS = SQL_ADD = SQL_SUM = SQL(" + ")
SQL_DIV = SQL(" / ")
SQL_SUB = SQL(" - ")

SQL_AND = SQL(" AND ")
SQL_OR = SQL(" OR ")
SQL_NOT = SQL(" NOT ")
SQL_ON = SQL(" ON ")

SQL_CASE = SQL(" CASE ")
SQL_WHEN = SQL(" WHEN ")
SQL_THEN = SQL(" THEN ")
SQL_ELSE = SQL(" ELSE ")
SQL_END = SQL(" END ")

SQL_CAST = SQL("CAST")
SQL_COMMA = SQL(", ")
SQL_CROSS_JOIN = ConcatSQL(SQL_CR, SQL("CROSS JOIN"), SQL_CR)
SQL_UNION_ALL = ConcatSQL(SQL_CR, SQL("UNION ALL"), SQL_CR)
SQL_UNION = ConcatSQL(SQL_CR, SQL("UNION"), SQL_CR)
SQL_LEFT_JOIN = ConcatSQL(SQL_CR, SQL("LEFT JOIN"), SQL_CR)
SQL_INNER_JOIN = ConcatSQL(SQL_CR, SQL("JOIN"), SQL_CR)
SQL_EMPTY_STRING = SQL("''")
SQL_ZERO = SQL(" 0 ")
SQL_ONE = SQL(" 1 ")
SQL_TRUE = SQL_ONE
SQL_FALSE = SQL_ZERO
SQL_NEG_ONE = SQL(" -1 ")
SQL_NULL = SQL(" NULL ")
SQL_IS_NULL = SQL(" IS NULL ")
SQL_IS_NOT_NULL = SQL(" IS NOT NULL ")
SQL_SELECT = ConcatSQL(SQL("SELECT"), SQL_CR)
SQL_SELECT_AS_STRUCT = ConcatSQL(SQL_CR, SQL("SELECT AS STRUCT"), SQL_CR)
SQL_DELETE = ConcatSQL(SQL_CR, SQL("DELETE"), SQL_CR)
SQL_CREATE = ConcatSQL(SQL_CR, SQL("CREATE TABLE"), SQL_CR)
SQL_INSERT = ConcatSQL(SQL_CR, SQL("INSERT INTO"), SQL_CR)
SQL_WITH = ConcatSQL(SQL_CR, SQL("WITH "))
SQL_FROM = ConcatSQL(SQL_CR, SQL("FROM"), SQL_CR)
SQL_WHERE = ConcatSQL(SQL_CR, SQL("WHERE"), SQL_CR)
SQL_GROUPBY = ConcatSQL(SQL_CR, SQL("GROUP BY"), SQL_CR)
SQL_ORDERBY = ConcatSQL(SQL_CR, SQL("ORDER BY"), SQL_CR)
SQL_VALUES = ConcatSQL(SQL_CR, SQL("VALUES"), SQL_CR)
SQL_DESC = SQL(" DESC ")
SQL_ASC = SQL(" ASC ")
SQL_LIMIT = ConcatSQL(SQL_CR, SQL("LIMIT"), SQL_CR)
SQL_UPDATE = ConcatSQL(SQL_CR, SQL("UPDATE"), SQL_CR)
SQL_SET = ConcatSQL(SQL_CR, SQL("SET"), SQL_CR)

SQL_ALTER_TABLE = SQL("ALTER TABLE ")
SQL_ADD_COLUMN = SQL(" ADD COLUMN ")
SQL_DROP_COLUMN = SQL(" DROP COLUMN ")
SQL_RENAME_COLUMN = SQL(" RENAME COLUMN ")
SQL_RENAME_TO = SQL(" RENAME TO ")

SQL_CONCAT = SQL(" || ")
SQL_AS = SQL(" AS ")
SQL_LIKE = SQL(" LIKE ")
SQL_ESCAPE = SQL(" ESCAPE ")
SQL_TO = SQL(" TO ")
SQL_OP = SQL("(")
SQL_CP = SQL(")")
SQL_IN = SQL(" IN ")
SQL_GT = SQL(" > ")
SQL_GE = SQL(" >= ")
SQL_EQ = SQL(" = ")
SQL_LT = SQL(" < ")
SQL_LE = SQL(" <= ")
SQL_NEG = SQL("-")
SQL_DOT = SQL(".")


class DB(object):
    """
    Quoting, or escaping, database entitiy names (columns, tables, etc) is database specific
    """

    def quote_column(self, *path):
        raise NotImplementedError()

    def db_type_to_json_type(self, type):
        raise NotImplementedError()


def sql_list(list_):
    return ConcatSQL(SQL_SPACE, JoinSQL(SQL_COMMA, list_), SQL_SPACE)


def sql_join(sep, list_):
    return JoinSQL(SQL_COMMA, list_)


def sql_iso(*sql):
    # isoLATE EXPRESSION
    return ConcatSQL(SQL_OP, SQL_CR, IndentSQL(sql), SQL_CR, SQL_CP)


def sql_cast(expr, type):
    return ConcatSQL(SQL_CAST, SQL_OP, expr, SQL_AS, TextSQL(type), SQL_CP)


def sql_concat_text(list_):
    """
    TEXT CONCATENATION WITH "||"
    """
    return JoinSQL(SQL_CONCAT, [sql_iso(l) for l in list_])


def sql_call(func_name, *parameters):
    return ConcatSQL(SQL(func_name), sql_iso(JoinSQL(SQL_COMMA, parameters)))


def sql_count(sql):
    return sql_call("COUNT", sql)


def sql_coalesce(list_):
    return sql_call("COALESCE", *list_)
