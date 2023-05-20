# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import unicode_literals

import base64

from mo_json import json2value
from mo_testing.fuzzytestcase import FuzzyTestCase

from mo_math import aes_crypto, randoms


class TestCrypto(FuzzyTestCase):
    def test_aes(self):
        aes_crypto.DEBUG = True

        aes_crypto.encrypt("this is a test", randoms.bytes(32))
        aes_crypto.encrypt("this is a longer test with more than 16bytes", randoms.bytes(32))
        aes_crypto.encrypt("", randoms.bytes(32))
        aes_crypto.encrypt("testing accented char àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ", randoms.bytes(32))
        aes_crypto.encrypt("testing accented char àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ", randoms.bytes(32))

    def test_aes_nothing(self):
        key = base642bytearray(u'nm5/wK20R45AUtetHJwHTdOigvGTxP7NcH/41YE8AZo=')
        encrypted = aes_crypto.encrypt("", key, salt=base642bytearray("AehqWt1OdEgPJhCx6uylyg=="))
        self.assertEqual(
            json2value(encrypted.decode('utf8')),
            json2value(u'{"type": "AES256", "length": 0, "salt": "AehqWt1OdEgPJhCx6uylyg=="}')
        )

    def test_aes_on_char(self):
        key = base642bytearray(u'nm5/wK20R45AUtetHJwHTdOigvGTxP7NcH/41YE8AZo=')
        encrypted = aes_crypto.encrypt("kyle", key, salt=base642bytearray("AehqWt1OdEgPJhCx6uylyg=="))
        self.assertEqual(
            json2value(encrypted.decode('utf8')),
            json2value(u'{"type": "AES256", "length": 4, "salt": "AehqWt1OdEgPJhCx6uylyg==", "data": "FXUGxdb9E+4UCKwsIT9ugQ=="}')
        )



def base642bytearray(value):
    if value == None:
        return bytearray(b"")
    else:
        return bytearray(base64.b64decode(value))