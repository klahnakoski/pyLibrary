# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import absolute_import, division, unicode_literals

import pandas as pd
import numpy as np

from jx_base.expressions import extend
from mo_dots import Null, coalesce, join_field, split_field, startswith_field
from mo_future import text
from mo_json.typed_encoder import TYPE_PREFIX
from mo_logs import Log


class Table(object):
    """
    REPRESENT A DATA CUBE
    Mimic multiple Panda's Dataframes
    """

    def __init__(self, values, reps, defs, num_rows, schema, max_definition_level=None):
        """
        :param values: dict from full name to list of values
        :param reps:  dict from full name to list of values
        :param defs: dict from full name to list of values
        :param num_rows: number of rows in the dataset
        :param schema: The complete SchemaTree
        """
        self.values = {untype_path(k): v for k, v in values.items()}
        self.reps = {untype_path(k): v for k, v in reps.items()}
        self.defs = {untype_path(k): v for k, v in defs.items()}
        self.index = Null
        self.num_rows = num_rows
        self.schema = schema

    def __getattr__(self, item):
        return getattr(self.values, item)

    def get_column(self, name):
        sub_schema = self.schema

        while '.' in sub_schema.more:
            sub_schema = sub_schema.more.get('.')

        for n in split_field(name):
            m = sub_schema.more
            if n in m:
                sub_schema = m.get(n)
            else:
                Log.error("{{name}} not found in schema", name=name)

            while '.' in sub_schema.more:
                sub_schema = sub_schema.more.get('.')

        return Column(
            name,
            self.values[name],
            self.reps[name],
            self.defs[name],
            self.num_rows,
            sub_schema,
            self.schema.max_repetition_level(name),
            self.schema.max_definition_level(name)
        )

    @property
    def columns(self):
        return self.values.keys()

    def __getitem__(self, item):
        if isinstance(item, text):
            sub_schema = self.schema
            for n in split_field(item):
                if n in sub_schema.more:
                    sub_schema = sub_schema.more.get(n)
                else:
                    sub_schema = sub_schema.values.get(n)

            return Table(
                {k: v for k, v in self.values.items() if startswith_field(k, item)},
                {k: v for k, v in self.reps.items() if startswith_field(k, item)},
                {k: v for k, v in self.defs.items() if startswith_field(k, item)},
                self.num_rows,
                sub_schema,
                self.max_definition_level
            )
        elif isinstance(item, slice):
            start = coalesce(item.start, 0)
            stop = coalesce(item.stop, self.num_rows)

            if start == 0 and stop == self.num_rows:
                return self

            first = 0
            last = 0
            counter = 0
            for i, r in enumerate(self.reps):
                if counter == start:
                    first = i
                elif counter == stop:
                    last = i
                    break
                if r == 0:
                    counter += 1

            return Table(
                {k: v[first:last] for k, v in self.values.items()},
                {k: v[first:last] for k, v in self.reps.items()},
                {k: v[first:last] for k, v in self.defs.items()},
                stop - start,
                self.schema
            )

    def __len__(self):
        return self.num_rows


class Column(object):
    """
    REPRESENT A DATA FRAME
    """

    def __init__(self, name, values, reps, defs, num_rows, schema, max_repetition_level, max_definition_level):
        self.name = name
        self._values = values
        self.reps = reps
        self.defs = defs
        self.num_rows = num_rows
        self.schema = schema
        self.max_repetition_level = max_repetition_level
        self.max_definition_level = max_definition_level

    def __len__(self):
        return self.num_rows

    @property
    def values(self):
        return np.array(self._values, self.schema.numpy_type)

    @property
    def dtype(self):
        return self.schema.numpy_type


eq_backup = pd.DataFrame.__eq__
ne_backup = pd.DataFrame.__ne__


@extend(pd.DataFrame)
def __eq__(self, other):
    try:
        return eq_backup(self, other)
    except Exception as e:
        return False


@extend(pd.DataFrame)
def __ne__(self, other):
    try:
        return ne_backup(self, other)
    except Exception as e:
        return True

def untype_path(path):
    return join_field(c for c in split_field(path) if not c.startswith(TYPE_PREFIX))


@extend(pd.DataFrame)
def __data__(self):
    return {k:v for k,v in self.to_dict().items()}


