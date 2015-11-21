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
from __future__ import division
from __future__ import absolute_import
from datetime import datetime
from pyLibrary import strings

from pyLibrary.strings import expand_template
from pyLibrary.testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.times.dates import Date


class TestDate(FuzzyTestCase):


    def test_mising_milli(self):
        date = Date("2015-10-04 13:53:11", '%Y-%m-%d %H:%M:%S.%f')
        expecting = Date(datetime(2015, 10, 04, 13, 53, 11))
        self.assertEqual(date, expecting)


