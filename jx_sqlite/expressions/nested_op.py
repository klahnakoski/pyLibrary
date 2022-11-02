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

from jx_base.expressions import QueryOp
from jx_base.expressions.nested_op import NestedOp as _NestedOp
from mo_imports import expect

QueryTable = expect("QueryTable")


class NestedOp(_NestedOp):
    def to_sql(self, schema):
        frum = schema.get_table(self.nested_path[0])
        # LEVERAGE QUERY OP ?
        query = QueryOp(
            select=self.select,
            frum=frum,
            where=self.where,
            sort=self.sort,
            limit=self.limit,
        )

        engine = QueryTable(name="testing", container=schema.container)
        index_to_column, ordered_sql, primary_doc_details = engine.to_sql(query)

        return ordered_sql
