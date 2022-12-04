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

from jx_base.expressions._utils import (
    operators,
    jx_expression,
    _jx_expression,
)
from jx_base.language import BaseExpression, ID, is_expression
from jx_base.models.container import Container
from mo_dots import is_data, is_container
from mo_future import items as items_
from mo_imports import expect
from mo_json import BOOLEAN, value2json, T_IS_NULL, JxType
from mo_logs import Log

TRUE, FALSE, Literal, is_literal, MissingOp, NotOp, NULL, Variable, AndOp = expect(
    "TRUE",
    "FALSE",
    "Literal",
    "is_literal",
    "MissingOp",
    "NotOp",
    "NULL",
    "Variable",
    "AndOp",
)


class Expression(BaseExpression):
    _data_type:JxType = T_IS_NULL
    has_simple_form = False

    def __init__(self, *args):
        self.simplified = False
        # SOME BASIC VERIFICATION THAT THESE ARE REASONABLE PARAMETERS
        bad = [t for t in args if t != None and not is_expression(t)]
        if bad:
            Log.error("Expecting an expression, not {{bad}}", bad=bad)

    @classmethod
    def get_id(cls):
        return getattr(cls, ID)

    @classmethod
    def define(cls, expr):
        """
        GENERAL SUPPORT FOR BUILDING EXPRESSIONS FROM JSON EXPRESSIONS
        OVERRIDE THIS IF AN OPERATOR EXPECTS COMPLICATED PARAMETERS
        :param expr: Data representing a JSON Expression
        :return: parse tree
        """

        try:
            lang = cls.lang
            items = items_(expr)
            for item in items:
                op, term = item
                full_op = operators.get(op)
                if full_op:
                    class_ = lang.ops[full_op.get_id()]
                    clauses = {k: jx_expression(v) for k, v in expr.items() if k != op}
                    break
            else:
                if not items:
                    return NULL
                raise Log.error(
                    "{{operator|quote}} is not a known operator", operator=expr
                )

            if term == None:
                return class_(**clauses)
            elif is_container(term):
                terms = [jx_expression(t) for t in term]
                return class_(*terms, **clauses)
            elif is_data(term):
                items = items_(term)
                if class_.has_simple_form:
                    if len(items) == 1:
                        k, v = items[0]
                        return class_(Variable(k), Literal(v), **clauses)
                    else:
                        Log.error("add define method to {{op}}}", op=class_.__name__)
                else:
                    return class_(_jx_expression(term, lang), **clauses)
            else:
                if op in ["literal", "date", "offset"]:
                    return class_(term, **clauses)
                else:
                    return class_(_jx_expression(term, lang), **clauses)
        except Exception as cause:
            Log.warning(
                "programmer error expr = {{value|quote}}", value=expr, cause=cause
            )
            Log.error(
                "programmer error expr = {{value|quote}}", value=expr, cause=cause
            )

    @property
    def name(self):
        return self.__class__.__name__

    def __data__(self):
        raise NotImplementedError

    def vars(self):
        raise Log.error("{{type}} has no `vars` method", type=self.__class__.__name__)

    def map(self, map):
        raise Log.error("{{type}} has no `map` method", type=self.__class__.__name__)

    def missing(self, lang):
        """
        THERE IS PLENTY OF OPPORTUNITY TO SIMPLIFY missing EXPRESSIONS
        OVERRIDE THIS METHOD TO SIMPLIFY
        :return:
        """
        if self.type == BOOLEAN:
            Log.error("programmer error")
        return self.lang.MissingOp(self)

    def exists(self):
        """
        THERE IS PLENTY OF OPPORTUNITY TO SIMPLIFY exists EXPRESSIONS
        OVERRIDE THIS METHOD TO SIMPLIFY
        :return:
        """
        return self.lang.NotOp(self.missing(self.lang)).partial_eval(self.lang)

    def invert(self, lang):
        """
        :return: TRUE IF FALSE
        """
        better = self.partial_eval(lang)
        if better is TRUE:
            return FALSE
        elif better is FALSE:
            return TRUE
        else:
            return NotOp(better)

    def partial_eval(self, lang):
        """
        ATTEMPT TO SIMPLIFY THE EXPRESSION:
        PREFERABLY RETURNING A LITERAL, BUT MAYBE A SIMPLER EXPRESSION, OR self IF NOT POSSIBLE
        """
        return self

    def to_jx(self, schema):
        """
        :param schema: THE SCHEMA USED TO INTERPRET THIS EXPRESSION
        :return: SOMETHING BETTER
        """
        return self

    def apply(self, container: Container, group_by):
        """
        Apply this expression over the container of data

        q.apply(c) <=> c.query(q)

        :return: data, depending on the expression
        """
        return container.query(self, group_by)

    @property
    def type(self) -> JxType:
        return self._data_type

    def __eq__(self, other):
        try:
            if self.get_id() != other.get_id():
                return False
        except Exception:
            return False
        Log.note("this is slow on {{type}}", type=self.__class__.__name__)
        return self.__data__() == other.__data__()

    def __contains__(self, item):
        return item.__rcontains__(self)

    def __rcontains__(self, superset):
        """
        :param superset: A FILTER (RETURNS BOOLEAN)
        :return: True IF superset RETURNS True WHEN self RETURNS True
        """
        return self.__eq__(superset)

    def __str__(self):
        return value2json(self.__data__(), pretty=True)

    def __repr__(self):
        return value2json(self.__data__())

    def __getattr__(self, item):
        Log.error(
            "{{type}} object has no attribute {{item}}, did you .register_ops() for"
            " {{type}}?",
            type=self.__class__.__name__,
            item=item,
        )
