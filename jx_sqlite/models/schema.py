# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#

from __future__ import absolute_import, division, unicode_literals

from typing import Set, Tuple

from jx_base import Column
from jx_base.models.nested_path import NestedPath
from jx_base.queries import get_property_name
from jx_sqlite.expressions._utils import SQL_ARRAY_KEY
from jx_sqlite.utils import GUID, untyped_column, untype_field, typed_column
from mo_dots import (
    concat_field,
    relative_field,
    set_default,
    startswith_field,
    endswith_field,
)
from mo_json import EXISTS, OBJECT, STRUCT, to_jx_type, JxType
from mo_logs import Log


class Schema(object):
    """
    A Schema MAPS ALL COLUMNS IN SNOWFLAKE FROM THE PERSPECTIVE OF A SINGLE TABLE (a nested_path)
    """

    def __init__(self, nested_path: NestedPath, snowflake):
        if not isinstance(nested_path, list) or nested_path[-1] == ".":
            Log.error(
                "Expecting full nested path so we can track the tables, and deal with"
                " abiguity in the event the names are not typed"
            )
        self.nested_path = nested_path
        self.snowflake = snowflake

    def __getitem__(self, item):
        output = self.snowflake.namespace.columns.find(self.nested_path[0], item)
        return output

    def get_table(self, table_name):
        nested_path = [table_name] + self.nested_path
        return self.snowflake.get_table(nested_path)

    def get_table_name(self):
        return self.nested_path[0]

    def get_column_name(self, column):
        """
        RETURN THE COLUMN NAME, FROM THE PERSPECTIVE OF THIS SCHEMA
        :param column:
        :return: NAME OF column
        """
        relative_name = relative_field(column.name, self.nested_path[0])
        return get_property_name(relative_name)

    @property
    def namespace(self):
        return self.snowflake.namespace

    @property
    def container(self):
        return self.snowflake.container

    def get_many_relations(self, path):
        """
        :param path:
        :return: (remainder_field, relation) pair from this table to many table
        """

        if path.startswith(".."):
            # ASSUME RELATIVE TO PATH IN THIS SNOWFLAKE
            abs_field = concat_field(
                self.snowflake.fact_name,
                self.nested_path[0],
                typed_column(path, SQL_ARRAY_KEY),
            )
            if abs_field.startswith(".."):
                Log.error("Can not accept {{path}} past facts", path=path)
            names = [abs_field]
        else:
            typed_name = typed_column(path, SQL_ARRAY_KEY)
            names = [
                typed_name,  # TYPED TABLE
                path,  # REGULAR RELATIONAL TABLE
                concat_field(self.nested_path[0], typed_name),  # FULL NAME
                concat_field(self.nested_path[0], path),
            ]
        relations = self.snowflake.get_relations()
        matches = [
            (relative_field(n, r.many_table), r)
            for n in names
            for r in relations
            if startswith_field(n, r.many_table)
               and r.ones_table == self.get_table_name()
        ]
        if not matches:
            return None, None
        elif len(matches) == 1:
            return matches[0]
        else:
            raise NotImplementedError(
                "not sure how to handle two paths to same ones table"
            )

    def get_one_relations(self, relative_path):
        many_name = self.get_table_name()
        return [
            r
            for r in self.snowflake.get_relations()
            if r.many_table == many_name and endswith_field(r.ones_table, relative_path)
        ]

    def keys(self):
        """
        :return: ALL DYNAMIC TYPED COLUMN NAMES
        """
        return set(c.name for c in self.columns)

    def get_primary_keys(self):
        return self.snowflake.namespace.columns.primary_keys.get(self.nested_path[0], tuple())

    @property
    def columns(self):
        return self.snowflake.namespace.columns.find(self.snowflake.fact_name)

    @property
    def get_type(self) -> JxType:
        return JxType(**{
            c.es_column: to_jx_type(c.json_type)
            for c in self.snowflake.namespace.get_columns(self.nested_path[0])
            if c.json_type not in [OBJECT, EXISTS]
        })

    def get_columns(self, prefix):
        full_name, _ = untyped_column(concat_field(
            relative_field(self.nested_path[0], self.snowflake.fact_name), prefix
        ))
        return set(
            c
            for c in self.snowflake.namespace.get_columns(self.nested_path[0])
            for k, t in [untyped_column(c.name)]
            if startswith_field(k, prefix)
            if c.json_type not in [OBJECT, EXISTS]
        )

    def leaves(self, prefix) -> Set[Tuple[str, Column]]:
        for np in self.nested_path:
            full_name = concat_field(np, prefix)
            candidates = self.columns
            output = set(
                (untype_field(relative_field(k, full_name))[0], c)
                for c in candidates
                if c.json_type not in [OBJECT, EXISTS]
                # if startswith_field(np, c.nested_path[0])
                for k in [c.name, c.es_column]
                if startswith_field(k, full_name) and k != GUID or k == full_name
            )
            if output:
                return output
        return set()

    def map_to_sql(self, var=""):
        """
        RETURN A MAP FROM THE RELATIVE AND ABSOLUTE NAME SPACE TO COLUMNS
        """
        origin = self.nested_path[0]
        if startswith_field(var, origin) and origin != var:
            var = relative_field(var, origin)
        fact_dict = {}
        origin_dict = {}
        for k, cs in self.namespace.items():
            for c in cs:
                if c.json_type in STRUCT:
                    continue

                if startswith_field(get_property_name(k), var):
                    origin_dict.setdefault(c.names[origin], []).append(c)

                    if origin != c.nested_path[0]:
                        fact_dict.setdefault(c.name, []).append(c)
                elif origin == var:
                    origin_dict.setdefault(
                        concat_field(var, c.names[origin]), []
                    ).append(c)

                    if origin != c.nested_path[0]:
                        fact_dict.setdefault(concat_field(var, c.name), []).append(c)

        return set_default(origin_dict, fact_dict)
