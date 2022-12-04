# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import absolute_import, division, unicode_literals

from unittest import skipIf, skip

from tests.test_jx import BaseTestCase, TEST_TABLE, global_settings


class TestAggOps(BaseTestCase):

    def test_boolean_in_expression(self):
        test = {
            "data": [
                {"result": {"ok": True}},
                {"result": {"ok": True}},
                {"result": {"ok": True}},
                {"result": {"ok": True}},
                {"result": {"ok": False}},
                {"result": {"ok": False}},
                {"result": {"ok": False}},
                {"result": {"ok": False}},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": {
                    "name": "failures",
                    "aggregate": "sum",
                    "value": {"when": {"eq": {"result.ok": "F"}}, "then": 1, "else": 0},
                },
            },
            "expecting_list": {"meta": {"format": "value"}, "data": 4},
        }

        self.utils.execute_tests(test)

    def test_boolean_in_expression2(self):
        test = {
            "data": [
                {"result": {"ok": True}},
                {"result": {"ok": True}},
                {"result": {"ok": True}},
                {"result": {"ok": True}},
                {"result": {"ok": False}},
                {"result": {"ok": False}},
                {"result": {"ok": False}},
                {"result": {"ok": False}},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": {
                    "name": "failures",
                    "aggregate": "sum",
                    "value": {
                        "when": {"eq": {"result.ok": False}},
                        "then": 1,
                        "else": 0,
                    },
                },
            },
            "expecting_list": {"meta": {"format": "value"}, "data": 4},
        }

        self.utils.execute_tests(test)

    @skipIf(global_settings.use == "sqlite", "broken")
    def test_select_agg_mult_w_when(self):
        test = {
            "data": [
                {"a": 0, "b": False},  # 0*1
                {"a": 1, "b": False},  # 1*1 = 1
                {"a": 2, "b": True},  # 2*0
                {"a": 3, "b": False},  # 3*1 = 3
                {"a": 4, "b": True},  # 4*0
                {"a": 5, "b": False},  # 5*1 = 5
                {"a": 6, "b": True},  # 6*0
                {"a": 7, "b": True},  # 7*0
                {"a": 8},  # COUNTED, "b" IS NOT true  # 8*1 = 8
                {"b": True},  # NOT COUNTED              null * 0 = null
                {"b": False},  # COUNTED                 null * 1 = null
            ],
            "query": {
                "from": TEST_TABLE,
                "select": {
                    "name": "ab",
                    "value": {"mult": ["a", {"when": "b", "then": 0, "else": 1}]},
                    "aggregate": "sum",
                },
            },
            "expecting_list": {"meta": {"format": "value"}, "data": 17},
        }
        self.utils.execute_tests(test)

    def test_simplest(self):
        test = {
            "data": [{"a": i} for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": {"aggregate": "count"}
            },
            "expecting_list": {
                "meta": {"format": "value"}, "data": 30
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["count"],
                "data": [[30]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "count": 30
                }
            }
        }
        self.utils.execute_tests(test)

    def test_max(self):
        test = {
            "data": [{"a": i*2} for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": {"value": "a", "aggregate": "max"}
            },
            "expecting_list": {
                "meta": {"format": "value"}, "data": 58
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a"],
                "data": [[58]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "a": 58
                }
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use == "sqlite", "not expected to pass yet")
    def test_median(self):
        test = {
            "data": [{"a": i**2} for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": {"value": "a", "aggregate": "median"}
            },
            "expecting_list": {
                "meta": {"format": "value"}, "data": 210.5
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a"],
                "data": [[210.5]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "a": 210.5
                }
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use == "sqlite", "not expected to pass yet")
    def test_percentile(self):
        test = {
            "data": [{"a": i**2} for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": {"value": "a", "aggregate": "percentile", "percentile": 0.90}
            },
            "expecting_list": {
                "meta": {"format": "value"}, "data": 702.5
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a"],
                "data": [[702.5]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "a": 702.5
                }
            }
        }
        self.utils.execute_tests(test, places=1.5)  # 1.5 approx +/- 3%

    @skipIf(global_settings.use=="sqlite", "not expected to pass yet")
    def test_both_percentile(self):
        test = {
            "data": [{"a": i**2} for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    {"name": "a", "value": "a", "aggregate": "percentile", "percentile": 0.90},
                    {"name": "b", "value": "a", "aggregate": "median"}
                ]
            },
            "expecting_list": {
                "meta": {"format": "value"},
                "data": {"a": 703.5, "b": 210.5}
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a", "b"],
                "data": [[703.5, 210.5]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "a": 703.5,
                    "b": 210.5
                }
            }
        }
        self.utils.execute_tests(test, places=1.5)  # 1.5 approx +/- 3%

    @skipIf(global_settings.use == "sqlite", "not expected to pass yet")
    def test_stats(self):
        test = {
            "data": [{"a": i**2} for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": {"value": "a", "aggregate": "stats"}
            },
            "expecting_list": {
                "meta": {"format": "value"}, "data": {
                    "count": 30,
                    "std": 259.76901064,
                    "min": 0,
                    "max": 841,
                    "sum": 8555,
                    "median": 210.5,
                    "sos": 4463999,
                    "var": 67479.93889,
                    "avg": 285.1666667
                }
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a"],
                "data": [[{
                    "count": 30,
                    "std": 259.76901064,
                    "min": 0,
                    "max": 841,
                    "sum": 8555,
                    "median": 210.5,
                    "sos": 4463999,
                    "var": 67479.93889,
                    "avg": 285.1666667
                }]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "a": {
                        "count": 30,
                        "std": 259.76901064,
                        "min": 0,
                        "max": 841,
                        "sum": 8555,
                        "median": 210.5,
                        "sos": 4463999,
                        "var": 67479.93889,
                        "avg": 285.1666667
                    }
                }
            }
        }
        self.utils.execute_tests(test, places=2)

    def test_bad_percentile(self):
        test = {
            "data": [{"a": i**2} for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": {"value": "a", "aggregate": "percentile", "percentile": "0.90"}
            },
            "expecting_list": {
                "meta": {"format": "value"}, "data": 681.3
            }
        }

        self.assertRaises("Expecting `percentile` to be a float", self.utils.execute_tests, test)

    def test_many_aggs_on_one_column(self):
        # ES WILL NOT ACCEPT TWO (NAIVE) AGGREGATES ON SAME FIELD, COMBINE THEM USING stats AGGREGATION
        test = {
            "data": [{"a": i*2} for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    {"name": "maxi", "value": "a", "aggregate": "max"},
                    {"name": "mini", "value": "a", "aggregate": "min"},
                    {"name": "count", "value": "a", "aggregate": "count"}
                ]
            },
            "expecting_list": {
                "meta": {"format": "value"},
                "data": {"mini": 0, "maxi": 58, "count": 30}
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["mini", "maxi", "count"],
                "data": [
                    [0, 58, 30]
                ]
            }
        }
        self.utils.execute_tests(test)

    def test_simplest_on_value(self):
        test = {
            "data": list(range(30)),
            "query": {
                "from": TEST_TABLE,
                "select": {"aggregate": "count"}
            },
            "expecting_list": {
                "meta": {"format": "value"}, "data": 30
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["count"],
                "data": [[30]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "count": 30
                }
            }
        }
        self.utils.execute_tests(test)

    def test_max_on_value(self):
        test = {
            "data": [i*2 for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": {"value": ".", "aggregate": "max"}
            },
            "expecting_list": {
                "meta": {"format": "value"},
                "data": 58
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["max"],
                "data": [[58]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "max": 58
                }
            }
        }
        self.utils.execute_tests(test)

    def test_max_object_on_value(self):
        test = {
            "data": [{"a": i*2} for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": [{"value": "a", "aggregate": "max"}]
            },
            "expecting_list": {
                "meta": {"format": "value"}, "data": {"a": 58}
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["a"],
                "data": [[58]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "a": 58
                }
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use == "sqlite", "sqlite does not have a median function")
    def test_median_on_value(self):
        test = {
            "data": [i**2 for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": {"value": ".", "aggregate": "median"}
            },
            "expecting_list": {
                "meta": {"format": "value"}, "data": 210.5
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["median"],
                "data": [[210.5]]
            },
            "expecting_cube": {
                "meta": {"format": "cube"},
                "edges": [],
                "data": {
                    "median": 210.5
                }
            }
        }
        self.utils.execute_tests(test, places=2)

    def test_many_aggs_on_value(self):
        # ES WILL NOT ACCEPT TWO (NAIVE) AGGREGATES ON SAME FIELD, COMBINE THEM USING stats AGGREGATION
        test = {
            "data": [i*2 for i in range(30)],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    {"name": "maxi", "value": ".", "aggregate": "max"},
                    {"name": "mini", "value": ".", "aggregate": "min"},
                    {"name": "count", "value": ".", "aggregate": "count"}
                ]
            },
            "expecting_list": {
                "meta": {"format": "value"},
                "data": {"mini": 0, "maxi": 58, "count": 30}
            },
            "expecting_table": {
                "meta": {"format": "table"},
                "header": ["mini", "maxi", "count"],
                "data": [
                    [0, 58, 30]
                ]
            }
        }
        self.utils.execute_tests(test)

    def test_cardinality(self):
        test = {
            "data": [
                {"a": 1, "b": "x"},
                {"a": 1, "b": "x"},
                {"a": 2, "b": "x"},
                {"a": 2, "d": "x"},
                {"a": 3, "d": "x"},
                {"a": 3, "d": "x"},
                {"a": 3, "d": "x"}
            ],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    {"value": "a", "aggregate": "cardinality"},
                    {"value": "b", "aggregate": "cardinality"},
                    {"value": "c", "aggregate": "cardinality"},
                    {"value": "d", "aggregate": "cardinality"}
                ]
            },
            "expecting_list": {
                "meta": {"format": "value"},
                "data": {"a": 3, "b": 1, "c": 0, "d": 1}
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use == "sqlite", "broken")
    def test_max_on_tuple(self):
        test = {
            "data": [
                {"a": 1, "b": 2},
                {"a": 1, "b": 1},
                {"a": 2, "b": 1},
                {"a": 2, "b": 2},
                {"a": 3, "b": 1},
                {"a": 3, "b": 2},
                {"a": 3, "b": 3},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    {"name": "max", "value": ["a", "b"], "aggregate": "max"},
                    {"name": "min", "value": ["a", "b"], "aggregate": "min"}
                ]
            },
            "expecting_list": {
                "meta": {"format": "value"},
                "data": {"max": [3, 3], "min": [1, 1]}
            }
        }
        self.utils.execute_tests(test)

    @skipIf(global_settings.use == "sqlite", "broken")
    def test_max_on_tuple2(self):
        test = {
            "data": [
                {"a": None, "b": True},
                {"a": None, "b": False},
                {"a": "a", "b": True},
                {"a": "a", "b": False},
                {"a": "b", "b": True},
                {"a": "b", "b": False},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    {"name": "max", "value": ["a", "b"], "aggregate": "max"},
                    {"name": "min", "value": ["a", "b"], "aggregate": "min"}
                ]
            },
            "expecting_list": {
                "meta": {"format": "value"},
                "data": {"max": ["b", True], "min": ["a", False]}
            }
        }
        self.utils.execute_tests(test)

    @skip("broken")
    def test_union(self):
        test = {
            "data": [
                {"b": "a"},
                {"b": "b"},
                {"b": "c"},
                {"b": "d"},
                {"b": "e"},
                {"b": "f"},
                {"b": "g"},
                {"b": "h"},
                {"b": "i"},
                {"b": "j"},
                {"b": "x"},
                {"b": "x"},
                {"b": "x"},
                {"b": "y"},
                {"b": "y"},
                {"b": "y"},
                {"b": "z"}
            ],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    {"value": "b", "aggregate": "union"}
                ]
            },
            "expecting_list": {
                "meta": {"format": "value"},
                "data": {"b": {"x", "y", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "z"}}
            }
        }
        self.utils.execute_tests(test)

    def test_booleans_can_be_summed(self):
        test = {
            "data": [
                {"a": None, "b": True},
                {"a": None, "b": False},
                {"a": "a", "b": True},
                {"a": "a", "b": False},
                {"a": "b", "b": True},
                {"a": "b", "b": False},
            ],
            "query": {
                "from": TEST_TABLE,
                "select": [
                    {"value": "b", "aggregate": "sum"},
                    {"name": "a", "value": {"eq": {"a": "a"}}, "aggregate": "sum"}
                ]
            },
            "expecting_list": {
                "meta": {"format": "value"},
                "data": {"b": 3, "a": 2}
            }
        }
        self.utils.execute_tests(test)
