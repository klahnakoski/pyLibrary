# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE


class SqlSelectAllFromOp(Expression):
    """
    REPRESENT ALL RECORDS IN A TABLE AS AN EXPRESSION
    SELECT * FROM table
    """

    def __init__(self, table):
        Expression.__init__(self)
        self.simplified = True
        self.table = table

    @property
    def type(self):
        return {c.es_column: str(JxType(c.type)) for c in self.table.schema.columns}

    def __data__(self):
        return {"sql.select_all_from": [self.lhs.__data__(), self.rhs.__data__()]}

    def missing(self, lang):
        return FALSE

    def __eq__(self, other):
        return other is self
