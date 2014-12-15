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
import unittest
from pyLibrary.debugs.logs import Log
from pyLibrary.maths import Math


class TestJSON(unittest.TestCase):
    def test_isnumber(self):
        assert Math.is_number(9999999999000)

if __name__ == '__main__':
    try:
        Log.start()
        unittest.main()
    finally:
        Log.stop()
