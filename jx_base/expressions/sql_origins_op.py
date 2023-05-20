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
from jx_base.expressions.sql_left_joins_op import SqlLeftJoinsOp, Source
from jx_base.expressions._utils import TYPE_CHECK


class SqlOriginsOp(Expression):
    """
    Point to the particular table in the left-join tree for naming context
    """

    def __init__(self, root: SqlLeftJoinsOp, origin: Source):
        if TYPE_CHECK:
            if not isinstance(origin, Source):
                logger.error("expecting source")

        Expression.__init__(self)
        self.root = root  # ROOT OF THE TREE (FACT TABLE)
        self.origin = origin  # PARTICULAR NODE IN TREE

    @property
    def type(self):
        return self.root.type

    def __str__(self):
        return self.root.frum._start_str(self.origin)
