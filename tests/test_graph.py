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

from mo_json import value2json

from mo_graphs.graph import Graph
from mo_testing.fuzzytestcase import FuzzyTestCase
from mo_graphs import Edge
from mo_graphs.algorithms import dominator_tree, LOOPS, ROOTS


class TestGraph(FuzzyTestCase):

    def test_single(self):
        edges = [
            (1, 1)
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)
        expected = [{(ROOTS, 1)}]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))

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
        self.assertEqual(dom.edges, expected, "not found " + value2json(dom.edges))

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
        expected = [
            {(LOOPS, 1), (1, 2), (1, 3), (1, 4), (1, 10), (4, 5)}
        ]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))

    def test_double_loop_A(self):
        edges = [
            (1, 2),
            (2, 1),
            (2, 3),
            (3, 1),
            (1, "A")
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)
        expected = [
            {(LOOPS, 2), (2, 3), (3, 1), (1, "A")},
            {(LOOPS, 1), (2, 3), (1, 2), (1, "A")},
            {(LOOPS, 2), (LOOPS, 3), (2, 1), (1, "A")},
            {(LOOPS, 1), (LOOPS, 2), (LOOPS, 3), (1, "A")}
        ]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))

    def test_double_loop_B(self):
        edges = [
            (1, 2),
            (2, 1),
            (2, 3),
            (3, 1),
            (2, "B")
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)
        expected = [
            {(LOOPS, 1), (2, 3), (1, 2), (2, "B")},
            {(LOOPS, 1), (LOOPS, 3), (1, 2), (2, "B")}
        ]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))

    def test_double_loop_C(self):
        edges = [
            (1, 2),
            (2, 1),
            (2, 3),
            (3, 1),
            (3, "C")
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)
        expected = [
            {(LOOPS, 1), (1, 2), (2, 3), (3, "C")}
        ]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))

    def test_triple_loop_A(self):
        edges = [
            (1, 2),
            (2, 1),
            (2, 3),
            (3, 1),
            (1, 4),
            (4, 2),
            (1, "A")
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)
        expected = [
            {(LOOPS, 2), (1, 4), (2, 3), (3, 1), (1, "A")},
            {(LOOPS, 2), (LOOPS, 4), (2, 3), (3, 1), (1, "A")},
            {(LOOPS, 1), (LOOPS, 2), (LOOPS, 3), (LOOPS, 4), (1, "A")},
            {(LOOPS, 2), (LOOPS, 3), (LOOPS, 4), (2, 1), (1, "A")}
        ]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))

    def test_triple_loop_B(self):
        edges = [
            (1, 2),
            (2, 1),
            (2, 3),
            (3, 1),
            (1, 4),
            (4, 2),
            (2, "B")
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)
        expected = [
            {(LOOPS, 1), (LOOPS, 2), (LOOPS, 3), (LOOPS, 4), (2, "B")},
            {(LOOPS, 1), (LOOPS, 3), (LOOPS, 4), (1, 2), (2, "B")}
        ]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))

    def test_triple_loop_C(self):
        edges = [
            (1, 2),
            (2, 1),
            (2, 3),
            (3, 1),
            (1, 4),
            (4, 2),
            (3, "C")
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)
        expected = [
            {(LOOPS, 1), (LOOPS, 2), (LOOPS, 4), (2, 3), (3, "C")},
            {(LOOPS, 1), (LOOPS, 4), (1, 2), (2, 3), (3, "C")},
            {(LOOPS, 2), (LOOPS, 3), (1, 4), (2, 1), (3, "C")}
        ]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))

    def test_triple_loop_D(self):
        edges = [
            (1, 2),
            (2, 1),
            (2, 3),
            (3, 1),
            (1, 4),
            (4, 2),
            (4, "D")
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)

        expected = [
            {(LOOPS, 2), (2, 3), (3, 1), (1, 4), (4, "D")},
            {(LOOPS, 1), (LOOPS, 2), (LOOPS, 3), (1, 4), (4, "D")},
            {(LOOPS, 2), (LOOPS, 3), (2, 1), (1, 4), (4, "D")}
        ]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))

    def test_from_two_loops(self):
        edges = [
            (1, 2),
            (2, 1),
            (3, 4),
            (4, 3),
            (1, "A"),
            (3, "A")
        ]

        g = Graph(int)
        for e in edges:
            g.add_edge(Edge(*e))

        dom = dominator_tree(g)
        expected = [
            {(LOOPS, 2), (LOOPS, 4), (2, 1), (4, 3), (1, "A")}
        ]
        self.assertTrue(any(dom.edges == e for e in expected), "not found " + value2json(dom.edges))
