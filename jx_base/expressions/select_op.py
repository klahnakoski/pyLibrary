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

from typing import Dict, Tuple, Iterable

from jx_base.expressions._utils import TYPE_CHECK, simplified
from jx_base.expressions.aggregate_op import AggregateOp
from jx_base.expressions.expression import jx_expression, Expression, _jx_expression
from jx_base.expressions.from_op import FromOp
from jx_base.expressions.leaves_op import LeavesOp
from jx_base.expressions.sql_select_op import SqlSelectOp
from jx_base.expressions.literal import Literal
from jx_base.expressions.null_op import NULL
from jx_base.expressions.variable import Variable
from jx_base.language import is_op
from jx_base.models.container import Container
from jx_base.utils import is_variable_name
from mo_dots import (
    to_data,
    coalesce,
    Data,
    split_field,
    join_field,
    literal_field,
    is_missing, is_many,
)
from mo_future import is_text, text
from mo_imports import export
from mo_json import union_type
from mo_logs import Log
from mo_math import is_number


class SelectOp(Expression):
    has_simple_form = True

    def __init__(self, frum, *terms: Tuple[Dict[str, Expression]]):
        """
        :param terms: list OF {"name":name, "value":value} DESCRIPTORS
        """
        if TYPE_CHECK and (
                not all(isinstance(term, dict) for term in terms[1:])
                or any(term.get("name") is None for term in terms)
        ):
            Log.error("expecting list of dicts with 'name' and 'aggregate' property")
        Expression.__init__(self, None)
        self.frum = frum
        self.terms = terms
        self._data_type = union_type(*(t["name"] + t["value"].type for t in terms))

    @classmethod
    def define(cls, expr):
        frum, *selects = to_data(expr).select
        frum = _jx_expression(frum, cls.lang)

        terms = []
        for t in to_data(selects):
            if is_op(t, SelectOp):
                terms.extend(t.terms)
            elif is_text(t):
                if not is_variable_name(t):
                    Log.error(
                        "expecting {{value}} a simple dot-delimited path name", value=t
                    )
                terms.append({"name": t, "value": _jx_expression(t, cls.lang)})
            elif t.aggregate:
                # AGGREGATES ARE INSERTED INTO THE CALL CHAIN
                if t.value == None:
                    Log.error(
                        "expecting select parameters to have name and value properties"
                    )
                elif t.name == None:
                    if is_text(t.value):
                        if not is_variable_name(t.value):
                            Log.error(
                                "expecting {{value}} a simple dot-delimited path name",
                                value=t.value,
                            )
                        else:
                            terms.append({
                                "name": t.value,
                                "value": AggregateOp(FromOp(_jx_expression(t.value, cls.lang)), t.aggregate),
                            })
                    else:
                        Log.error("expecting a name property")
                else:
                    terms.append({"name": t.name, "value": AggregateOp(FromOp(_jx_expression(t.value, cls.lang)), t.aggregate)})
            elif t.name == None:
                if t.value == None:
                    Log.error(
                        "expecting select parameters to have name and value properties"
                    )
                elif is_text(t.value):
                    if not is_variable_name(t.value):
                        Log.error(
                            "expecting {{value}} a simple dot-delimited path name",
                            value=t.value,
                        )
                    else:
                        terms.append({
                            "name": t.value,
                            "value": _jx_expression(t.value, cls.lang),
                        })
                else:
                    Log.error("expecting a name property")
            else:
                terms.append({"name": t.name, "value": jx_expression(t.value)})
        return SelectOp(frum, *terms)

    @simplified
    def partial_eval(self, lang):
        new_terms = []
        diff = False
        for name, expr in self:
            new_expr = expr.partial_eval(lang)
            if new_expr is expr:
                new_terms.append({
                    "name": name,
                    "value": expr
                })
                continue
            diff = True

            if expr is NULL:
                continue
            elif is_op(expr, SelectOp):
                for t_name, t_value in expr.terms:
                    new_terms.append({
                        "name": concat_field(name, t_name),
                        "value": t_value
                    })
            else:
                new_terms.append({
                    "name": name,
                    "value": new_expr
                })
                diff = True
        if diff:
            return SelectOp(self.frum, new_terms)
        else:
            return self

    def apply(self, container: Container, group_by):
        result = self.frum.apply(container, group_by)
        results = tuple(
            {"name": name, "value": value.apply(result, group_by)}
            for name, value in self
        )
        # GROUP BY COMMON TABLE
        return SqlSelectOp(result, results)

    def __iter__(self) -> Iterable[Tuple[str, Expression, str]]:
        """
        :return:  return iterator of (name, value) tuples
        """
        for term in self.terms:
            yield term["name"], term["value"]

    def __data__(self):
        return {"select": [self.frum.__data__()] + [
            {"name": name, "value": value.__data__()}
            for name, value in self
        ]}

    def vars(self):
        return set(v for term in self.terms for v in term['value'].vars())

    def map(self, map_):
        return SelectOp(self.frum, *(
            {"name": name, "value": value.map(map_), "aggregate": agg.map(map_)}
            for name, value in self
        ))


def normalize_one(frum, select):
    if is_text(select):
        if select == "*":
            return SelectOp(self.frum, *({
                "name": ".",
                "value": LeavesOp(Variable(".")),
                "aggregate": NULL,
            }))
        select = Data(value=select)
    else:
        select = to_data(select)
        unexpected = select.keys() - {
            "name",
            "value",
            "default",
            "aggregate",
            "percentile",
        }
        if unexpected:
            Log.error(
                "Expecting a select clause with `value` property.  Unexpected"
                " property: {{unexpected}}",
                unexpected=unexpected,
            )
        if is_missing(select.value) and is_missing(select.aggregate):
            # EXPLICIT REQUEST FOR NOTHING
            return select_nothing

    canonical = {"aggregate": NULL}

    name = select.name
    value = select.value
    aggregate = select.aggregate

    if not value:
        canonical["name"] = coalesce(name, aggregate)
        canonical["value"] = jx_expression(".", schema=schema)
        canonical["aggregate"] = aggregate

        if not canonical["name"] and len(select):
            Log.error(BAD_SELECT, select=select)
    elif is_text(value):
        if value == ".":
            canonical["name"] = coalesce(name, aggregate, ".")
            canonical["value"] = jx_expression(value, schema=schema)
        elif value.endswith(".*"):
            root_name = value[:-2]
            canonical["name"] = coalesce(name, root_name)
            value = jx_expression(root_name, schema=schema)
            if not is_op(value, Variable):
                Log.error("do not know what to do")
            canonical["value"] = LeavesOp(value, prefix=select.prefix)
        elif value.endswith("*"):
            root_name = value[:-1]
            path = split_field(root_name)

            canonical["name"] = coalesce(name, aggregate, join_field(path[:-1]))
            expr = jx_expression(root_name, schema=schema)
            if not is_op(expr, Variable):
                Log.error("do not know what to do")
            canonical["value"] = LeavesOp(
                expr, prefix=Literal((select.prefix or "") + path[-1] + ".")
            )
        else:
            canonical["name"] = coalesce(name, value.lstrip("."), aggregate)
            canonical["value"] = jx_expression(value, schema=schema)

    elif is_number(value):
        canonical["name"] = coalesce(name, text(value))
        canonical["value"] = jx_expression(value, schema=schema)
    else:
        canonical["name"] = coalesce(name, value, aggregate)
        canonical["value"] = jx_expression(value, schema=schema)

    default = jx_expression(select.default, schema=schema)
    if select.aggregate:
        agg_op = canonical["aggregate"] = canonical_aggregates[aggregate](canonical["value"])
        if default:
            agg_op.default = default
        if select.percentile:
            if not isinstance(select.pecentile, float):
                Log.error("Expecting `percentile` to be a float")
            agg_op.percentile = select.percentile
    elif default:
        canonical["value"] = CoalesceOp(canonical["value"], default)

    if format != "list" and canonical["name"] != ".":
        canonical["name"] = literal_field(canonical["name"])

    return SelectOp(self.frum, canonical)


export("jx_base.expressions.variable", SelectOp)


def _normalize_selects(frum, selects) -> SelectOp:
    if frum == None or is_text(frum) or is_many(frum):
        if is_many(selects):
            if len(selects) == 0:
                return select_nothing
            else:
                terms = [
                    t
                    for s in selects
                    for t in SelectOp
                    .normalize_one(frum, s)
                    .terms
                ]
        else:
            return SelectOp(frum, normalize_one(frum, select))
    elif is_many(selects):
        terms = [
            ss
            for s in selects
            for ss in SelectOp
            .normalize_one(s, frum=frum, format=format, schema=schema)
            .terms
        ]
    else:
        Log.error("should not happen")
        terms = normalize_one(frum, select).terms
        t0 = terms[0]
        t0["column_name"], t0["name"] = t0["name"], "."

    # ENSURE NAMES ARE UNIQUE
    exists = set()
    for s in terms:
        name = s["name"]
        if name in exists:
            Log.error("{{name}} has already been defined", name=name)
        exists.add(name)

    return SelectOp(frum, terms)