# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

import datetime
import unittest
from util.cnv import CNV
from util.logs import Log


class TestJSON(unittest.TestCase):
    def test_date(self):
        output = CNV.object2JSON({"test": datetime.date(2013, 11, 13)})
        Log.note("JSON = {{json}}", {"json": output})


    def test_unicode1(self):
        output = CNV.object2JSON({"comment": u"Open all links in the current tab, except the pages opened from external apps â€” open these ones in new windows"})
        if not isinstance(output, unicode):
            Log.error("expecting unicode json")

    def test_unicode2(self):
        output = CNV.object2JSON({"comment": "testing accented char Å•Ã¡Ã¢ÄƒÃ¤ÄºÄ‡Ã§ÄÃ©Ä™Ã«Ä›Ã­Ã®ÄÄ‘Å„ÅˆÃ³Ã´Å‘Ã¶Ã·Å™Å¯ÃºÅ±Ã¼Ã½Å£Ë™"})
        if not isinstance(output, unicode):
            Log.error("expecting unicode json")

    def test_unicode3(self):
        output = CNV.object2JSON({"comment": u"testing accented char Å•Ã¡Ã¢ÄƒÃ¤ÄºÄ‡Ã§ÄÃ©Ä™Ã«Ä›Ã­Ã®ÄÄ‘Å„ÅˆÃ³Ã´Å‘Ã¶Ã·Å™Å¯ÃºÅ±Ã¼Ã½Å£Ë™"})
        if not isinstance(output, unicode):
            Log.error("expecting unicode json")

    def test_double(self):
        test = {"value": 5.2025595183536973e-07}
        output = CNV.object2JSON(test)
        if output != u'{"value": 5.202559518353697e-07}':
            Log.error("expecting correct value")



if __name__ == '__main__':
    unittest.main()
