# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

# MIMICS THE requests API (http://docs.python-requests.org/en/latest/)
# DEMANDS data IS A JSON-SERIALIZABLE STRUCTURE
# WITH ADDED default_headers THAT CAN BE SET USING mo_logs.settings
# EG
# {"debug.constants":{
#     "mo_http.http.default_headers":{"From":"klahnakoski@mozilla.com"}
# }}


from __future__ import absolute_import, division

from unittest import TestCase

from mo_http import http


class Tests(TestCase):
    def test_call_google(self):
        http.get("https://google.com")
