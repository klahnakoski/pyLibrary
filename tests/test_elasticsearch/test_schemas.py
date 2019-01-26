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

from unittest import skip

from mo_testing.fuzzytestcase import FuzzyTestCase
from pyLibrary.env import elasticsearch


class TestSchemas(FuzzyTestCase):
    @skip("not valid")
    def test_diff(self):
        branch_props = elasticsearch.Cluster(host="http://localhost").get_index("debug_active_data", "active_data").get_properties()
        debug_props = elasticsearch.Cluster(host="http://localhost").get_index("debug", "bz_etl").get_properties()

        elasticsearch.diff_schema(branch_props, debug_props)


