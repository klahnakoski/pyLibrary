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
from pyLibrary.maths import crypto
from pyLibrary import convert
from pyLibrary.maths.randoms import Random


class TestCrypto(unittest.TestCase):
    def test_aes(self):
        crypto.DEBUG = True

        key = convert.bytes2base64(Random.bytes(32))

        crypto.encrypt("this is a test", Random.bytes(32))
        crypto.encrypt("this is a longer test with more than 16bytes", Random.bytes(32))
        crypto.encrypt("", Random.bytes(32))
        crypto.encrypt(convert.latin12unicode(b"testing accented char àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"), Random.bytes(32))
        crypto.encrypt("testing accented char àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ", Random.bytes(32))


