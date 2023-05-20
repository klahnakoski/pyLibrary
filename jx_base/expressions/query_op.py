# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from copy import copy
from importlib import import_module

import mo_math
from mo_dots import (
    Data,
    FlatList,
    Null,
    is_container,
    is_data,
    is_list,
    set_default,
    from_data,
    is_many,
    dict_to_data,
    to_data,
    list_to_data,
    tail_field,
)
from mo_logs import Log
from mo_math import AND, UNION

from jx_base.domains import DefaultDomain, Domain, SetDomain
from jx_base.expressions._utils import jx_expression
from jx_base.expressions.expression import Expression
from jx_base.expressions.false_op import FALSE
from jx_base.expressions.filter_op import _normalize_where
from jx_base.expressions.leaves_op import LeavesOp
from jx_base.expressions.script_op import ScriptOp
from jx_base.expressions.select_op import (
    SelectOp,
    _normalize_selects,
    SelectOne,
)
from jx_base.expressions.variable import Variable
from jx_base.language import is_expression, is_op
from jx_base.models.dimensions import Dimension
from jx_base.utils import is_variable_name, coalesce, delist, enlist
from mo_future import is_text
from mo_imports import expect
from mo_imports import export
from mo_json.typed_encoder import untype_path

Column = expect("Column")

BAD_SELECT = "Expecting `value` or `aggregate` in select clause not {{select}}"
DEFAULT_LIMIT = 10
MAX_LIMIT = 10000
DEFAULT_SELECT = (SelectOne(".", Variable(".")),)


class QueryOp(Expression):
    __slots__ = [
        "frum",
        "edges",
        "window",
        "format",
        "chunk_size",
        "destination",
    ]

    op = "from"

    def __init__(
        self,
        frum,
        select=None,
        edges=None,
        groupby=None,
        where=None,
        sort=None,
        limit=None,
        window=None,
        format=None,
        chunk_size=None,
        destination=None,
    ):
        Expression.__init__(self, None)
        self.frum = frum
        self.select: SelectOp = select if select is not None else SelectOp(frum, DEFAULT_SELECT)
        self.edges = edges
        self.groupby = groupby
        self.window = window
        self.where = where
        self.sort = sort
        self.limit = limit
        self.format = format
        self.chunk_size = chunk_size
        self.destination = destination

    @classmethod
    def define(cls, expr):
        expr = to_data(expr)
        frum = expr["from"]
        output = QueryOp(frum=frum, format=expr.format, chunk_size=expr.chunk_size, destination=expr.destination,)

        _import_temper_limit()
        limit = temper_limit(expr.limit, expr)
        if mo_math.is_integer(limit) and limit < 0:
            Log.error("Expecting limit >= 0")
        output.limit = jx_expression(limit)

        select = from_data(expr).get("select")
        if expr.groupby and expr.edges:
            raise Log.error("You can not use both the `groupby` and `edges` clauses in the same query!")
        elif expr.edges:
            if select is None:
                select = [{"aggregate": "count"}]
            elif is_many(expr.select):
                pass
            else:
                select = [expr.select]

            output.edges = _normalize_edges(expr.edges, limit=output.limit)
            output.groupby = Null
        elif expr.groupby:
            if select is None:
                select = [{"aggregate": "count"}]
            elif is_many(expr.select):
                pass
            else:
                select = [expr.select]

            output.edges = Null
            output.groupby = _normalize_groupby(expr.groupby, limit=output.limit)
        else:
            output.edges = Null
            output.groupby = Null

        if is_many(select):
            output.select = _normalize_selects(frum, select)
        elif select or is_data(select):
            output.select = normalize_one(select, frum, expr.format)
            if expr.format == "list":
                output.select.terms[0]["name"] = "."
        elif expr.edges or expr.groupby:
            output.select = DEFAULT_SELECT
        else:
            output.select = normalize_one(".", frum, expr.format)

        output.where = _normalize_where(expr.where)
        output.window = [_normalize_window(w) for w in enlist(expr.window)]
        output.sort = _normalize_sort(expr.sort)

        return output

    @staticmethod
    def wrap(query, container):
        """
        TODO: SHOULD BE QueryOp.define()
        NORMALIZE QUERY SO IT CAN STILL BE JSON
        """
        if is_op(query, QueryOp) or query == None:
            return query
        query = to_data(query)

        frum = query["from"]
        # FIND THE TABLE IN from CLAUSE
        base_name, query_path = tail_field(frum)
        snowflake = container.namespace.get_snowflake(base_name)
        frum = snowflake.get_table(query_path)
        schema = frum.schema

        output = QueryOp(frum=frum, format=query.format, chunk_size=query.chunk_size, destination=query.destination,)

        _import_temper_limit()
        limit = temper_limit(query.limit, query)
        if mo_math.is_integer(limit) and limit < 0:
            Log.error("Expecting limit >= 0")
        output.limit = jx_expression(limit)

        select = from_data(query).get("select")
        if query.groupby and query.edges:
            raise Log.error("You can not use both the `groupby` and `edges` clauses in the same query!")
        elif query.edges:
            if select is None:
                select = [{"aggregate": "count"}]
            elif is_many(query.select):
                pass
            else:
                select = [query.select]

            output.edges = _normalize_edges(query.edges, limit=output.limit, schema=schema)
            output.groupby = Null
        elif query.groupby:
            if select is None:
                select = [{"aggregate": "count"}]
            elif is_many(query.select):
                pass
            else:
                select = [query.select]

            output.edges = Null
            output.groupby = _normalize_groupby(query.groupby, limit=output.limit, schema=schema)
        else:
            output.edges = Null
            output.groupby = Null

        if is_many(select):
            output.select = _normalize_selects(frum, select)
        elif select or is_data(select):
            output.select = normalize_one(frum, select)
            if query.format == "list":
                output.select.terms[0]["name"] = "."
        elif query.edges or query.groupby:
            output.select = DEFAULT_SELECT
        else:
            output.select = SelectOp(frum, {"name": ".", "value": Variable(".")})

        output.where = _normalize_where(query.where)
        output.window = [_normalize_window(w) for w in enlist(query.window)]
        output.sort = _normalize_sort(query.sort)

        return output

    def __data__(self):
        return {
            "from": self.frum.__data__(),
            "select": self.select.___data__(),
            "edges": [e.__data__() for e in self.edges],
            "groupby": [g.__data__() for g in self.groupby],
            "window": [w.__data__() for w in self.window],
            "where": self.where.__data__(),
            "sort": self.sort.__data__(),
            "limit": self.limit.__data__(),
        }

    def copy(self):
        return QueryOp(
            frum=copy(self.frum),
            select=copy(self.select),
            edges=copy(self.edges),
            groupby=copy(self.groupby),
            window=copy(self.window),
            where=copy(self.where),
            sort=copy(self.sort),
            limit=copy(self.limit),
            format=copy(self.format),
        )

    def vars(self):
        """
        :return: variables in query
        """

        def edges_get_all_vars(e):
            output = set()
            if is_text(e.value):
                output.add(e.value)
            if is_expression(e.value):
                output |= e.value.vars()
            if e.domain.key:
                output.add(e.domain.key)
            if e.domain.where:
                output |= e.domain.where.vars()
            if e.range:
                output |= e.range.min.vars()
                output |= e.range.max.vars()
            if e.domain.partitions:
                for p in e.domain.partitions:
                    if p.where:
                        output |= p.where.vars()
            return output

        output = set()
        try:
            output |= self.frum.vars()
        except Exception:
            pass

        output |= self.select.vars()
        for s in enlist(self.edges):
            output |= edges_get_all_vars(s)
        for s in enlist(self.groupby):
            output |= edges_get_all_vars(s)
        output |= self.where.vars()
        for s in enlist(self.sort):
            output |= s.value.vars()

        try:
            output |= UNION(e.vars() for e in self.window)
        except Exception:
            pass

        return output

    def map(self, map_):
        def map_select(s, map_):
            return set_default({"value": s.value.map(map_)}, s)

        def map_edge(e, map_):
            partitions = delist([set_default({"where": p.where.map(map_)}, p) for p in e.domain.partitions])

            domain = copy(e.domain)
            domain.where = e.domain.where.map(map_)
            domain.partitions = partitions

            edge = copy(e)
            edge.value = e.value.map(map_)
            edge.domain = domain
            if e.range:
                edge.range.min = e.range.min.map(map_)
                edge.range.max = e.range.max.map(map_)
            return edge

        if is_list(self.select):
            select = list_to_data([map_select(s, map_) for s in self.select])
        else:
            select = map_select(self.select, map_)

        return QueryOp(
            frum=self.frum.map(map_),
            select=select,
            edges=list_to_data([map_edge(e, map_) for e in self.edges]),
            groupby=list_to_data([g.map(map_) for g in self.groupby]),
            window=list_to_data([w.map(map_) for w in self.window]),
            where=self.where.map(map_),
            sort=list_to_data([map_select(s, map_) for s in enlist(self.sort)]),
            limit=self.limit,
            format=self.format,
        )

    def missing(self, lang):
        return FALSE

    @property
    def columns(self):
        return enlist(self.select) + coalesce(self.edges, self.groupby)

    @property
    def query_path(self):
        return self.frum.schema.query_path

    @property
    def column_names(self):
        return enlist(self.select).name + self.edges.name + self.groupby.name

    def __getitem__(self, item):
        if item == "from":
            return self.frum
        return Data.__getitem__(self, item)

    def copy(self):
        output = object.__new__(QueryOp)
        for s in QueryOp.__slots__:
            setattr(output, s, getattr(self, s))
        return output

    def __data__(self):
        output = dict_to_data({s: getattr(self, s) for s in QueryOp.__slots__})
        return output


def temper_limit(limit, query):
    return coalesce(query.limit, 10)


def _import_temper_limit():
    global temper_limit
    try:
        temper_limit = import_module("jx_elasticsearch.es52").temper_limit
    except Exception as e:
        pass


def _normalize_edges(edges, limit, schema=None):
    return list_to_data([
        n for ie, e in enumerate(enlist(edges)) for n in _normalize_edge(e, ie, limit=limit, schema=schema)
    ])


def _normalize_edge(edge, dim_index, limit, schema=None):
    """
    :param edge: Not normalized edge
    :param dim_index: Dimensions are ordered; this is this edge's index into that order
    :param schema: for context
    :return: a normalized edge
    """
    if not edge:
        Log.error("Edge has no value, or expression is empty")
    elif is_text(edge):
        if schema:
            leaves = delist([l for r, l in schema.leaves(edge)])
            if not leaves or is_container(leaves):
                return [Data(
                    name=edge,
                    value=jx_expression(edge, schema=schema),
                    allowNulls=True,
                    dim=dim_index,
                    domain=_normalize_domain(None, limit),
                )]
            elif isinstance(leaves, Column):
                return [Data(
                    name=edge,
                    value=jx_expression(edge, schema=schema),
                    allowNulls=True,
                    dim=dim_index,
                    domain=_normalize_domain(domain=leaves, limit=limit, schema=schema),
                )]
            elif is_list(leaves.fields) and len(leaves.fields) == 1:
                return [Data(
                    name=leaves.name,
                    value=jx_expression(leaves.fields[0], schema=schema),
                    allowNulls=True,
                    dim=dim_index,
                    domain=leaves.getDomain(),
                )]
            else:
                return [Data(name=leaves.name, allowNulls=True, dim=dim_index, domain=leaves.getDomain(),)]
        else:
            return [Data(
                name=edge,
                value=jx_expression(edge, schema=schema),
                allowNulls=True,
                dim=dim_index,
                domain=DefaultDomain(),
            )]
    else:
        edge = to_data(edge)
        if not edge.name and not is_text(edge.value):
            Log.error("You must name compound and complex edges: {{edge}}", edge=edge)

        if is_container(edge.value) and not edge.domain:
            # COMPLEX EDGE IS SHORT HAND
            domain = _normalize_domain(schema=schema)
            domain.dimension = Data(fields=edge.value)

            return [Data(
                name=edge.name,
                value=jx_expression(edge.value, schema=schema),
                allowNulls=bool(coalesce(edge.allowNulls, True)),
                dim=dim_index,
                domain=domain,
            )]

        domain = _normalize_domain(edge.domain, schema=schema)

        return [Data(
            name=coalesce(edge.name, edge.value),
            value=jx_expression(edge.value, schema=schema),
            range=_normalize_range(edge.range),
            allowNulls=bool(coalesce(edge.allowNulls, True)),
            dim=dim_index,
            domain=domain,
        )]


def _normalize_groupby(groupby, limit, schema=None):
    if groupby == None:
        return None
    output = list_to_data([n for e in enlist(groupby) for n in _normalize_group(e, None, limit, schema=schema)])
    for i, o in enumerate(output):
        o.dim = i
    if any(o == None for o in output):
        Log.error("not expected")
    return output


def _normalize_group(edge, dim_index, limit, schema=None):
    """
    :param edge: Not normalized groupby
    :param dim_index: Dimensions are ordered; this is this groupby's index into that order
    :param schema: for context
    :return: a normalized groupby
    """
    if is_text(edge):
        if edge == "*":
            return list_to_data([{
                "name": ".",
                "value": LeavesOp(Variable(".")),
                "allowNulls": True,
                "dim": dim_index,
                "domain": DefaultDomain(limit=limit, desc=edge),
            }])
        elif edge.endswith(".*"):
            prefix = edge[:-2]
            return list_to_data([{
                "name": untype_path(prefix),
                "value": LeavesOp(Variable(prefix)),
                "allowNulls": True,
                "dim": dim_index,
                "domain": DefaultDomain(limit=limit, desc=edge),
            }])
        return list_to_data([{
            "name": edge,
            "value": jx_expression(edge, schema=schema),
            "allowNulls": True,
            "dim": dim_index,
            "domain": DefaultDomain(limit=limit, desc=edge),
        }])
    else:
        edge = to_data(edge)
        if edge.domain and edge.domain.type != "default":
            Log.error("groupby does not accept complicated domains")

        if not edge.name and not is_text(edge.value):
            Log.error("You must name compound edges: {{edge}}", edge=edge)

        return list_to_data([{
            "name": coalesce(edge.name, edge.value),
            "value": jx_expression(edge.value, schema=schema),
            "allowNulls": True,
            "dim": dim_index,
            "domain": DefaultDomain(limit=limit, desc=edge),
        }])


def _normalize_domain(domain=None, limit=None, schema=None):
    if not domain:
        return DefaultDomain(limit=limit)
    elif isinstance(domain, Column):
        if (
            domain.partitions and domain.multi <= 1
        ):  # MULTI FIELDS ARE TUPLES, AND THERE ARE TOO MANY POSSIBLE COMBOS AT THIS TIME
            return SetDomain(partitions=domain.partitions.limit(limit))
        else:
            return DefaultDomain(limit=limit)
    elif isinstance(domain, Dimension):
        return domain.getDomain()
    elif schema and is_text(domain) and schema[domain]:
        return schema[domain].getDomain()
    elif isinstance(domain, Domain):
        return domain

    return Domain(domain)


def _normalize_window(window, schema=None):
    v = window.value
    try:
        expr = jx_expression(v, schema=schema)
    except Exception:
        if hasattr(v, "__call__"):
            expr = v
        else:
            expr = ScriptOp(v)

    return Data(
        name=coalesce(window.name, window.value),
        value=expr,
        edges=[
            n for i, e in enumerate(enlist(window.edges)) for n in _normalize_edge(e, i, limit=None, schema=schema)
        ],
        sort=_normalize_sort(window.sort),
        aggregate=window.aggregate,
        range=_normalize_range(window.range),
        where=_normalize_where(window.where, schema=schema),
    )


def _normalize_range(range):
    if range == None:
        return None

    return Data(
        min=None if range.min == None else jx_expression(range.min),
        max=None if range.max == None else jx_expression(range.max),
        mode=range.mode,
    )


def _map_term_using_schema(master, path, term, schema_edges):
    """
    IF THE WHERE CLAUSE REFERS TO FIELDS IN THE SCHEMA, THEN EXPAND THEM
    """
    output = FlatList()
    for k, v in term.items():
        dimension = schema_edges[k]
        if isinstance(dimension, Dimension):
            domain = dimension.getDomain()
            if dimension.fields:
                if is_data(dimension.fields):
                    # EXPECTING A TUPLE
                    for local_field, es_field in dimension.fields.items():
                        local_value = v[local_field]
                        if local_value == None:
                            output.append({"missing": {"field": es_field}})
                        else:
                            output.append({"term": {es_field: local_value}})
                    continue

                if len(dimension.fields) == 1 and is_variable_name(dimension.fields[0]):
                    # SIMPLE SINGLE-VALUED FIELD
                    if domain.getPartByKey(v) is domain.NULL:
                        output.append({"missing": {"field": dimension.fields[0]}})
                    else:
                        output.append({"term": {dimension.fields[0]: v}})
                    continue

                if AND(is_variable_name(f) for f in dimension.fields):
                    # EXPECTING A TUPLE
                    if not isinstance(v, tuple):
                        Log.error("expecing {{name}}={{value}} to be a tuple", name=k, value=v)
                    for i, f in enumerate(dimension.fields):
                        vv = v[i]
                        if vv == None:
                            output.append({"missing": {"field": f}})
                        else:
                            output.append({"term": {f: vv}})
                    continue
            if len(dimension.fields) == 1 and is_variable_name(dimension.fields[0]):
                if domain.getPartByKey(v) is domain.NULL:
                    output.append({"missing": {"field": dimension.fields[0]}})
                else:
                    output.append({"term": {dimension.fields[0]: v}})
                continue
            if domain.partitions:
                part = domain.getPartByKey(v)
                if part is domain.NULL or not part.esfilter:
                    Log.error("not expected to get NULL")
                output.append(part.esfilter)
                continue
            else:
                Log.error("not expected")
        elif is_data(v):
            sub = _map_term_using_schema(master, path + [k], v, schema_edges[k])
            output.append(sub)
            continue

        output.append({"term": {k: v}})
    return {"and": output}


def _where_terms(master, where, schema):
    """
    USE THE SCHEMA TO CONVERT DIMENSION NAMES TO ES FILTERS
    master - TOP LEVEL WHERE (FOR PLACING NESTED FILTERS)
    """
    if is_data(where):
        if where.term:
            # MAP TERM
            try:
                output = _map_term_using_schema(master, [], where.term, schema.edges)
                return output
            except Exception as e:
                Log.error("programmer problem?", e)
        elif where.terms:
            # MAP TERM
            output = FlatList()
            for k, v in where.terms.items():
                if not is_container(v):
                    Log.error("terms filter expects list of values")
                edge = schema.edges[k]
                if not edge:
                    output.append({"terms": {k: v}})
                else:
                    if is_text(edge):
                        # DIRECT FIELD REFERENCE
                        return {"terms": {edge: v}}
                    try:
                        domain = edge.getDomain()
                    except Exception as e:
                        Log.error("programmer error", e)
                    fields = domain.dimension.fields
                    if is_data(fields):
                        or_agg = []
                        for vv in v:
                            and_agg = []
                            for local_field, es_field in fields.items():
                                vvv = vv[local_field]
                                if vvv != None:
                                    and_agg.append({"term": {es_field: vvv}})
                            or_agg.append({"and": and_agg})
                        output.append({"or": or_agg})
                    elif is_list(fields) and len(fields) == 1 and is_variable_name(fields[0]):
                        output.append({"terms": {fields[0]: v}})
                    elif domain.partitions:
                        output.append({"or": [domain.getPartByKey(vv).esfilter for vv in v]})
            return {"and": output}
        elif where["or"]:
            return {"or": [from_data(_where_terms(master, vv, schema)) for vv in where["or"]]}
        elif where["and"]:
            return {"and": [from_data(_where_terms(master, vv, schema)) for vv in where["and"]]}
        elif where["not"]:
            return {"not": from_data(_where_terms(master, where["not"], schema))}
    return where


def _normalize_sort(sort=None):
    """
    CONVERT SORT PARAMETERS TO A NORMAL FORM SO EASIER TO USE
    """

    if sort == None:
        return Null

    output = FlatList()
    for s in enlist(sort):
        if is_text(s):
            output.append({"value": jx_expression(s), "sort": 1})
        elif is_expression(s):
            output.append({"value": s, "sort": 1})
        elif mo_math.is_integer(s):
            output.append({"value": jx_expression({"offset": s}), "sort": 1})
        elif not s.sort and not s.value:
            if all(d in sort_direction for d in s.values()):
                # {field: direction} format:  eg {"machine_name": "desc"}
                for v, d in s.items():
                    output.append({
                        "value": jx_expression(v),
                        "sort": sort_direction[d],
                    })
            else:
                Log.error("`sort` clause must have a `value` property")
        else:
            output.append({
                "value": jx_expression(coalesce(s.value, s.field)),
                "sort": sort_direction[s.sort],
            })
    return output


sort_direction = {
    "asc": 1,
    "ascending": 1,
    "desc": -1,
    "descending": -1,
    "none": 0,
    1: 1,
    0: 0,
    -1: -1,
    None: 1,
}


export("jx_base.expressions.variable", QueryOp)
