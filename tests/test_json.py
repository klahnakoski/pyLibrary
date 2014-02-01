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
import datetime
import unittest
from util.cnv import CNV
from util.env.logs import Log


class TestJSON(unittest.TestCase):
    def test_date(self):
        output = CNV.object2JSON({"test": datetime.date(2013, 11, 13)})
        Log.note("JSON = {{json}}", {"json": output})


    def test_unicode1(self):
        output = CNV.object2JSON({"comment": u"Open all links in the current tab, except the pages opened from external apps â€” open these ones in new windows"})
        assert output == u'{"comment": "Open all links in the current tab, except the pages opened from external apps â€” open these ones in new windows"}'

        if not isinstance(output, unicode):
            Log.error("expecting unicode json")

    def test_unicode2(self):
        output = CNV.object2JSON({"comment": b"testing accented char àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"})

        assert output == u'{"comment": "testing accented char àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ"}'
        if not isinstance(output, unicode):
            Log.error("expecting unicode json")

    def test_unicode3(self):
        output = CNV.object2JSON({"comment": u"testing accented char ŕáâăäĺćçčéęëěíîďđńňóôőö÷řůúűüýţ˙"})
        assert output == u'{"comment": "testing accented char ŕáâăäĺćçčéęëěíîďđńňóôőö÷řůúűüýţ˙"}'
        if not isinstance(output, unicode):
            Log.error("expecting unicode json")

    def test_double(self):
        test = {"value": 5.2025595183536973e-07}
        output = CNV.object2JSON(test)
        if output != u'{"value": 5.202559518353697e-07}':
            Log.error("expecting correct value")

    def test_generator(self):
        test = {"value": (x for x in [])}
        output = CNV.object2JSON(test)
        if output != u'{"value": []}':
            Log.error("expecting correct value")


    # def test_odd_chars(self):
    #     {
    #         "priority": "p5",
    #         "product": "mozilla",
    #         "modified_by": "arunr@formerly-netscape.com.tld",
    #         "bug_status": "new",
    #         "reported_by": "arunr@formerly-netscape.com.tld",
    #         "bug_version_num": 1,
    #         "assigned_to": "nobody@mozilla.org",
    #         "short_desc": "testing accented char \u0155\xe1\xe2\u0103\xe4\u013a\u0107\xe7\u010d\xe9\u0119\xeb\u011b\xed\xee\u010f\u0111\u0144\u0148\xf3\xf4\u0151\xf6\xf7\u0159\u016f\xfa\u0171\xfc\xfd\u0163\u02d9",
    #         "created_ts": 895647600000,
    #         "created_by": "arunr@formerly-netscape.com.tld",
    #         "id": "384_895647600",
    #         "bug_id": 384,
    #         "version": "1998-03-31",
    #         "bug_severity": "enhancement",
    #         "expires_on": 904611043000,
    #         "rep_platform": "all",
    #         "modified_ts": 895647600000,
    #         "op_sys": "other",
    #         "everconfirmed": 1
    #     }

if __name__ == '__main__':
    unittest.main()
