# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

# from __future__ import unicode_literals
import random
from math import floor

from mo_testing.fuzzytestcase import FuzzyTestCase

import mo_math
from mo_math import randoms


class TestMath(FuzzyTestCase):
    def test_isnumber(self):
        assert mo_math.is_number(9999999999000)

    def test_mod(self):
        self.assertEqual(mo_math.mod(12, 12), 0)
        self.assertEqual(mo_math.mod(11, 12), 11)
        self.assertEqual(mo_math.mod(2, 12), 2)
        self.assertEqual(mo_math.mod(1, 12), 1)
        self.assertEqual(mo_math.mod(-0, 12), 0)
        self.assertEqual(mo_math.mod(-1, 12), 11)
        self.assertEqual(mo_math.mod(-2, 12), 10)
        self.assertEqual(mo_math.mod(-12, 12), 0)

    def test_floor(self):
        self.assertEqual(mo_math.floor(0, 1), 0)
        self.assertEqual(mo_math.floor(1, 1), 1)
        self.assertEqual(mo_math.floor(-1, 1), -1)
        self.assertEqual(mo_math.floor(0.1, 1), 0)
        self.assertEqual(mo_math.floor(1.1, 1), 1)
        self.assertEqual(mo_math.floor(-1.1, 1), -2)

        self.assertEqual(mo_math.floor(0, 2), 0)
        self.assertEqual(mo_math.floor(1, 2), 0)
        self.assertEqual(mo_math.floor(-1, 2), -2)
        self.assertEqual(mo_math.floor(0.1, 2), 0)
        self.assertEqual(mo_math.floor(1.1, 2), 0)
        self.assertEqual(mo_math.floor(-1.1, 2), -2)
        self.assertEqual(mo_math.floor(-10, 2), -10)

    def test_floor_mod_identity(self):
        for i in range(100):
            x = randoms.float()*200 - 100.0
            m = abs(random.gauss(0, 5))

            self.assertAlmostEqual(mo_math.floor(x, m)+mo_math.mod(x, m), x, places=7)

    def test_floor_mod_identity_w_ints(self):
        for i in range(100):
            x = randoms.float()*200 - 100.0
            m = floor(abs(random.gauss(0, 5)))

            if m == 0:
                self.assertEqual(mo_math.floor(x, m), None)
                self.assertEqual(mo_math.mod(x, m), None)
            else:
                self.assertAlmostEqual(mo_math.floor(x, m)+mo_math.mod(x, m), x, places=7)

    def test_round(self):
        self.assertAlmostEqual(mo_math.round(3.1415, digits=0), 1)
        self.assertAlmostEqual(mo_math.round(3.1415, digits=4), 3.142)
        self.assertAlmostEqual(mo_math.round(4, digits=0), 10)
        self.assertAlmostEqual(mo_math.round(11, digits=0), 10)
        self.assertAlmostEqual(mo_math.round(3.1415), 3)

    def test_random_hex(self):
        self.assertEqual(len(randoms.hex(5)), 5)
