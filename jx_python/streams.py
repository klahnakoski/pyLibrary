# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_json import JxType, JX_IS_NULL

from jx_base.expressions import GetOp, Literal, Variable
from jx_python.expression_factory import ExpressionFactory
from jx_python.expression_factory import factory

_get = object.__getattribute__


class Streams:
    """
    A STREAM OF OBJECTS
    """

    def __init__(self, values, factory, schema):
        self.values = values
        self.factory = factory
        self.schema: JxType = schema

    def __getattr__(self, item):
        if isinstance(item, str):
            return self.map(ExpressionFactory(
                GetOp(self.factory.expr, Literal(item)), self.factory.domain
            ))
        if isinstance(item, ExpressionFactory):
            return self.map(ExpressionFactory(
                GetOp(self.factory.expr, item.expr), self.factory.domain
            ))

    def map(self, accessor):
        fact = factory(accessor, self.factory.domain)
        return Streams(self.values, fact, self.schema)

    ###########################################################################
    # TERMINATORS
    ###########################################################################

    def to_list(self):
        func = self.factory.build()
        return func(self.values)


def stream(values):
    return Streams(
        values, ExpressionFactory(Variable("."), Typer(example=values)), JX_IS_NULL
    )
