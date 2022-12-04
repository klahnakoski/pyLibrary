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

from jx_base.expressions.and_op import AndOp
from jx_base.expressions.eq_op import EqOp
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.literal import ZERO
from jx_base.expressions.not_op import NotOp
from jx_base.expressions.null_op import NULL
from jx_base.expressions.or_op import OrOp
from jx_base.expressions.true_op import TRUE
from jx_base.expressions.variable import IDENTITY
from jx_base.language import is_op
from mo_dots import Null, startswith_field, coalesce, listwrap
from mo_imports import export, expect
from mo_json.types import T_BOOLEAN


class NestedOp(Expression):
    _data_type = T_BOOLEAN
    has_simple_form = False

    __slots__ = ["nested_path", "select", "where", "sort", "limit"]

    def __init__(self, *frum,  nested_path, select=None, where=TRUE, sort=Null, limit=NULL):
        select = select or SelectOp(frum, {"name": ".", "value": IDENTITY})
        Expression.__init__(self, [select, where])
        self.nested_path = nested_path
        self.select = select
        self.where = where
        self.sort = sort
        self.limit = limit

    def partial_eval(self, lang):
        if self.missing(lang) is TRUE:
            return NestedOp(nested_path=self.nested_path, where=FALSE)
        return NestedOp(
            self.nested_path,
            self.select.partial_eval(lang),
            self.where.partial_eval(lang),
            self.sort.partial_eval(lang),
            self.limit.partial_eval(lang),
        )

    def __and__(self, other):
        """
        MERGE TWO  NestedOp
        """
        if not is_op(other, NestedOp):
            return AndOp(self, other)

        # MERGE
        elif self.nested_path == other.frum:
            return NestedOp(
                self.nested_path,
                listwrap(self.select) + listwrap(other.select),
                AndOp(self.where, other.where),
                coalesce(self.sort, other.sort),
                coalesce(self.limit, other.limit),
            )

        # NEST
        elif startswith_field(other.frum.var, self.nested_path.var):
            # WE ACHIEVE INTERSECTION BY LIMITING OURSELF TO ONLY THE DEEP OBJECTS
            # WE ASSUME frum SELECTS WHOLE DOCUMENT, SO self.select IS POSSIBLE
            return NestedOp(other, self.select, self.where, self.sort, self.limit,)

        elif startswith_field(self.nested_path.var, other.frum.var):
            return NestedOp(self, other.select, other.where, other.sort, other.limit,)
        else:
            return AndOp(self, other)

    def __data__(self):
        return {"nested": {
            "path": self.nested_path.__data__(),
            "select": self.select.__data__(),
            "where": self.where.__data__(),
            "sort": self.sort.__data__(),
            "limit": self.limit.__data__(),
        }}

    def __eq__(self, other):
        return (
                is_op(other, NestedOp)
                and self.nested_path == other.nested_path
                and self.select == other.select
                and self.where == other.where
                and self.sort == other.sort
                and self.limit == other.limit
        )

    def vars(self):
        return (
            self.nested_path.vars()
            | self.select.vars()
            | self.where.vars()
            | self.sort.vars()
            | self.limit.vars()
        )

    def map(self, mapping):
        return NestedOp(
            path=self.nested_path.map(mapping),
            select=self.select.map(mapping),
            where=self.where.map(mapping),
            sort=self.sort.map(mapping),
            limit=self.limit.map(mapping),
        )

    def invert(self, lang):
        return self.missing(lang)

    def missing(self, lang):
        return OrOp(
            NotOp(self.where),
            # self.path.missing(lang), ASSUME PATH TO TABLES, WHICH ASSUMED TO HAVE DATA (EXISTS)
            # self.select.missing(lang),
            EqOp(self.limit, ZERO),
        ).partial_eval(lang)


export("jx_base.expressions.basic_in_op", NestedOp)
