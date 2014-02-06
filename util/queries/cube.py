# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import unicode_literals
from .. import struct
from ..collections.matrix import Matrix
from ..env.logs import Log
from ..struct import nvl, Struct


class Cube(Struct):
    def __init__(self, query=None):
        Struct.__init__(self)

        query = struct.wrap(query)
        # if edges == None:
        #     self.edges = [{"name": "index", "domain": {"type": "numeric", "min": 0, "max": len(data), "interval": 1}}]
        #     self.data = data
        #     self.select = columns
        #     return

        edges = [_normalize_edge(e) for e in struct.listwrap(query.edges)]

        select = query.select
        if isinstance(select, list):
            select = [_normalize_select(s) for s in select]
        else:
            select = _normalize_select(select)

        limit = query.limit
        sort = _normalize_sort(query.sort)

        self["from"] = (query["from"] if isinstance(query["from"], basestring) else Cube(query["from"]))
        self.name = query.name
        self.edges = edges
        self.select = select
        self.where = query.where
        self.limit = limit
        self.sort = sort

    def __len__(self):
        """
        RETURN DATA VOLUME
        """
        if not self.edges:
            return 1

        return len(self.data)

    def __iter__(self):
        return self.data.__iter__()

    def get_columns(self):
        return self.columns

    def groupby(self, edges, simple=False):
        """
        SLICE THIS CUBE IN TO ONES WITH LESS DIMENSIONALITY
        simple==True WILL HAVE GROUPS BASED ON PARTITION VALUE, NOT PARTITION OBJECTS
        """
        edges = struct.wrap([_normalize_edge(e) for e in struct.listwrap(edges)])
        remainder = [e for e in self.edges if e.value not in edges.value]

        if len(edges) + len(remainder) != len(self.edges):
            Log.error("can not find some edges to group by")

        #offsets WILL SERVE TO MASK DIMS WE ARE NOT GROUPING BY, AND SERVE AS RELATIVE INDEX FOR EACH COORDINATE
        offsets = [self.data.dims[i] if e in edges else 0 for i, e in enumerate(self.edges)]
        new_dim = []
        acc = 1
        for i in range(len(offsets)-1, -1, -1):
            if offsets[i] == 0:
                new_dim.insert(0, self.data.cube.dims[i])
            else:
                size = offsets[i]
                offsets[i] = acc
                acc *= size

        if not new_dim:
            output = [[None, None] for i in range(acc)]
            _stack(self.data.cube, 0, self.edges, offsets, 0, output, Struct(), simple)
        else:
            output = [[None, Matrix(new_dim)] for i in range(acc)]
            _groupby(self.data.cube, 0, self.edges, offsets, 0, output, Struct(), [], simple)

        return output


def _groupby(cube, depth, edges, intervals, offset, output, group, new_coord, simple):
    if not edges:
        output[offset][0] = group
        output[offset][1][new_coord] = cube

    edge = edges[depth]
    interval = intervals[depth]
    parts = edge.domain.partitions

    if interval:
        for i, c in enumerate(cube):
            g = group.copy()
            if simple:
                g[edge.name] = parts[i].value
            else:
                g[edge.name] = parts[i]
            _groupby(c, depth + 1, edges, intervals, offset + i * interval, output, g, new_coord, simple)
    else:
        for i, c in enumerate(cube):
            _groupby(c, depth + 1, edges, intervals, offset, output, group, new_coord + [i], simple)


def _stack(cube, depth, edges, intervals, offset, output, group, simple):
    """
    WHEN groupby ALL EDGES IN A CUBE, AND ZERO DIMENSIONS REMAIN
    """
    if depth == len(edges):
        output[offset][0] = group
        output[offset][1] = cube
        return

    edge = edges[depth]
    interval = intervals[depth]
    parts = edge.domain.partitions

    if len(cube) == 1:
        if simple:
            group[edge.name] = parts[0].value
        else:
            group[edge.name] = parts[0]
        _stack(cube[0], depth + 1, edges, intervals, offset, output, group, simple)
    else:
        for i, c in enumerate(cube):
            g = group.copy()
            if simple:
                g[edge.name] = parts[i].value
            else:
                g[edge.name] = parts[i]
            _stack(c, depth + 1, edges, intervals, offset + i * interval, output, g, simple)


class Domain():
    def __init__(self):
        pass


    def part2key(self, part):
        pass


    def part2label(self, part):
        pass


    def part2value(self, part):
        pass


def _normalize_select(select):
    if isinstance(select, basestring):
        return Struct(name=select, value=select)
    else:
        if not select.name:
            select = select.copy()
            select.name = select.value
            return select
        return select


def _normalize_edge(edge):
    if isinstance(edge, basestring):
        return Struct(name=edge, value=edge, domain=_normalize_domain())
    else:
        return Struct(name=nvl(edge.ame, edge.value), value=edge.value, domain=_normalize_domain(edge.domain))


def _normalize_domain(domain=None):
    if domain == None:
        return {"type": "default"}
    if not domain.name:
        domain = domain.copy()
        domain.name = domain.type
        return domain
    return domain


def _normalize_sort(sort=None):
    output = []
    for s in struct.listwrap(sort):
        if isinstance(s, basestring):
            output.append({"value": s, "sort": 1})
        else:
            output.append({"value": s.value, "sort": nvl(sort_direction[s.sort], 1)})
    return output


sort_direction = {
    "asc": 1,
    "desc": -1,
    "none": 0,
    1: 1,
    0: 0,
    -1: -1
}
