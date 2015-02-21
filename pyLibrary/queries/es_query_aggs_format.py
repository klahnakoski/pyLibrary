# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import unicode_literals
from __future__ import division
from copy import copy

from pyLibrary import convert
from pyLibrary.collections.matrix import Matrix
from pyLibrary.debugs.logs import Log
from pyLibrary.dot import Dict, literal_field, set_default
from pyLibrary.queries.cube import Cube
from pyLibrary.queries.es_query_aggs import count_dim, aggs_iterator, format_dispatch


def format_cube(decoders, aggs, start, query, select):
    new_edges = count_dim(aggs, decoders)
    dims = tuple(len(e.domain.partitions) + (0 if e.allowNulls is False else 1) for e in new_edges)
    matricies = [(s, Matrix(dims=dims, zeros=(s.aggregate == "count"))) for s in select]
    for row, agg in aggs_iterator(aggs, decoders):
        coord = tuple(d.get_index(row) for d in decoders)
        for s, m in matricies:
            # name = literal_field(s.name)
            if s.aggregate == "count" and s.value == None:
                m[coord] = agg.doc_count
            else:
                try:
                    if m[coord]:
                         Log.error("Not expected")
                    m[coord] = agg[literal_field(s.name)].value
                except Exception, e:
                    tuple(d.get_index(row) for d in decoders)
                    Log.error("", e)
    cube = Cube(query.select, new_edges, {s.name: m for s, m in matricies})
    cube.frum = query
    return cube


def format_table(decoders, aggs, start, query, select):
    new_edges = count_dim(aggs, decoders)
    header = new_edges.name + select.name

    def data():
        dims = tuple(len(e.domain.partitions) + (0 if e.allowNulls is False else 1) for e in new_edges)
        is_sent = Matrix(dims=dims, zeros=True)
        for row, agg in aggs_iterator(aggs, decoders):
            coord = tuple(d.get_index(row) for d in decoders)
            is_sent[coord] = 1

            output = [d.get_value(c) for c, d in zip(coord, decoders)]
            for s in select:
                if s.aggregate == "count" and s.value == None:
                    output.append(agg.doc_count)
                else:
                    output.append(agg[literal_field(s.name)].value)
            yield output

        # EMIT THE MISSING CELLS IN THE CUBE
        for c, v in is_sent:
            if not v:
                output = [d.get_value(c[i]) for i, d in enumerate(decoders)]
                for s in select:
                    if s.aggregate == "count":
                        output.append(0)
                    else:
                        output.append(None)
                yield output

    return Dict(
        meta={"format": "table"},
        header=header,
        data=list(data())
    )


def format_tab(decoders, aggs, start, query, select):
    table = format_table(decoders, aggs, start, query, select)

    def data():
        yield "\t".join(map(convert.string2quote, table.header))
        for d in table.data:
            yield "\t".join(map(convert.string2quote, d))

    return data()


def format_csv(decoders, aggs, start, query, select):
    table = format_table(decoders, aggs, start, query, select)

    def data():
        yield ", ".join(map(convert.string2quote, table.header))
        for d in table.data:
            yield ", ".join(map(convert.string2quote, d))

    return data()


def format_list(decoders, aggs, start, query, select):
    new_edges = count_dim(aggs, decoders)

    def data():
        dims = tuple(len(e.domain.partitions) + (0 if e.allowNulls is False else 1) for e in new_edges)
        is_sent = Matrix(dims=dims, zeros=True)
        for row, agg in aggs_iterator(aggs, decoders):
            coord = tuple(d.get_index(row) for d in decoders)
            is_sent[coord] = 1

            output = {e.name: d.get_value(c) for e, c, d in zip(query.edges, coord, decoders)}

            for s in select:
                if s.aggregate == "count" and s.value == None:
                    output[s.name] = agg.doc_count
                else:
                    output[s.name] = agg[literal_field(s.name)].value
            yield output

        # EMIT THE MISSING CELLS IN THE CUBE
        for c, v in is_sent:
            if not v:
                output = {d.edge.name: d.get_value(c[i]) for i, d in enumerate(decoders)}
                for s in select:
                    if s.aggregate == "count":
                        output[s.name] = 0
                yield output

    output = Dict(
        meta={"format": "list"},
        data=list(data())
    )
    return output


def format_line(decoders, aggs, start, query, select):
    list = format_list(decoders, aggs, start, query, select)

    def data():
        for d in list.data:
            yield convert.value2json(d)

    return data()


set_default(format_dispatch, {
    None: (format_cube, "application/json"),
    "cube": (format_cube, "application/json"),
    "table": (format_table, "application/json"),
    "list": (format_list, "application/json"),
    "csv": (format_csv, "text/csv"),
    "tab": (format_tab, "text/tab-separated-values"),
    "line": (format_line, "application/json")
})
