# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import unicode_literals

import unittest
from util import strings
from util.cnv import CNV
from util.env.files import File
from util.env.logs import Log, Except, extract_tb, ERROR
from util.queries.es_query import ESQuery


class TestESQuery(unittest.TestCase):
    # THE COMPLICATION WITH THIS TEST IS KNOWING IF
    # THE NESTED TERMS ARE andED TOGETHER ON EACH
    # NESTED DOCUMENT, OR *ANY* OF THE NESTED DOCUMENTS
    # "and" IS AMBIGUOUS, AND THE CONTEXT DB JOIN (OR ES "nested")
    # IS REQUIRED FOR DISAMBIGUATION.
    # USUALLY I WOULD SIMPLY FORCE THE QUERY TO APPLY TO THE NESTED
    # DOCUMENTS ONLY.  RETURNING THE PARENT DOCUMENT IS WHAT'S
    # AMBIGUOUS
    def test1(self):
        esq = ESQueryTester("private_bugs")

        esquery = esq.query({
            "from": "private_bugs",
            "select": "*",
            "where": {"and": [
                {"range": {"expires_on": {"gte": 1393804800000}}},
                {"range": {"modified_ts": {"lte": 1394074529000}}},
                {"term": {"changes.field_name": "assigned_to"}},
                {"term": {"changes.new_value": "klahnakoski"}}
            ]},
            "limit": 10
        })

        expecting = {}

        assert CNV.object2JSON(esquery, pretty=True) == CNV.object2JSON(expecting, pretty=True)


class ESQueryTester(object):
    def __init__(self, index):
        self.es = FakeES({
            "host":"example.com",
            "index":"index"
        })
        self.esq = ESQuery(self.es)

    def query(self, query):
        try:
            self.esq.query(query)
            return None
        except Exception, e:
            f = Except(ERROR, unicode(e), trace=extract_tb(1))
            try:
                details = str(f)
                query = CNV.JSON2object(strings.between(details, ">>>>", "<<<<"))
                return query
            except Exception, g:
                Log.error("problem", f)



class FakeES(object):

    def __init__(self, settings):
        self.settings = settings
        pass

    def search(self, query):
        Log.error("<<<<{{query}}>>>>", {"query":CNV.object2JSON(query)})

    def get_schema(self):
        return CNV.JSON2object(File("tests/resources/bug_version.json").read()).mappings.bug_version


