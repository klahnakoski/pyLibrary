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

from typing import Dict, Tuple

from jx_base.expressions import SqlLeftJoinsOp as _SqlLeftJoinsOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.sql_left_joins_op import Source
from jx_sqlite.expressions._utils import SQLang
from jx_sqlite.expressions.sql_script import SqlScript
from jx_sqlite.sqlite import (
    ConcatSQL,
    SQL_FROM,
    SQL_SELECT,
    sql_alias,
    sql_list,
)


class SqlLeftJoinsOp(_SqlLeftJoinsOp):
    def __init__(self, frum : Source, selects: Tuple[Dict[str, Expression]]):
        _SqlLeftJoinsOp.__init__(self, frum, selects)

    def to_sql(self, schema):





        return SqlScript(
            data_type=self.type,
            expr=ConcatSQL(
                SQL_SELECT,
                sql_list(
                    *(
                        sql_alias(s['value'].to_sql(schema), s['name'])
                        for s in self.selects
                    )
                ),
                SQL_FROM,
                self.frum.to_sql(schema),
            ),
            frum=self,
            miss=self.frum.missing(SQLang),
            schema=schema,
        )
