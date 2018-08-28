# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from mo_testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.graphs import Graph, Edge
from pyLibrary.graphs.algorithms import dominator_tree, LOOPS, ROOTS


class TestGraph(FuzzyTestCase):

    def test_dominator(self):

        edges = [
            (1, 2),
            (1, 3),
            (1, 4),
            (4, 5),
            (2, 10),
            (3, 10),
            (5, 10)
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)

        expected = {(ROOTS, 1), (1, 2), (1, 3), (1, 4), (1, 10), (4, 5)}

        self.assertEqual(dom.edges, expected)

    def test_dominator_loop(self):

        edges = [
            (1, 2),
            (1, 3),
            (1, 4),
            (4, 5),
            (2, 10),
            (3, 10),
            (5, 10),
            (10, 1)
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)

        expected = {(LOOPS, 1), (1, 2), (1, 3), (1, 4), (1, 10), (4, 5)}

        self.assertEqual(dom.edges, expected)

