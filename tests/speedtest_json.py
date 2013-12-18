# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from decimal import Decimal
import time
import json
from util import struct
from util.jsons import cPythonJSONEncoder, json_encoder
from util.logs import Log
from util.struct import Null


TARGET_RUNTIME = 10

EMPTY = (struct.wrap({}), 200000)
UNICODE = (struct.wrap(json._default_decoder.decode('{"key1": "\u0105\u0107\u017c", "key2": "\u0105\u0107\u017c"}')), 10000)
SIMPLE = (struct.wrap({
    'key1': 0,
    'key2': True,
    'key3': 'value',
    'key4': 3.141592654,
    'key5': 'string',
    "key6": Decimal(0.33)
}), 100000)
NESTED = (struct.wrap({
    'key1': 0,
    'key2': SIMPLE[0],
    'key3': 'value',
    'key4': None,
    'key5': SIMPLE[0],
    'key6': ["test", u"test2", 99],
    'key7': {1, 2.5, 3, 4},
    u'key': u'\u0105\u0107\u017c'
}), 100000)
HUGE = (struct.wrap([NESTED[0]] * 1000), 100)

cases = [
    'EMPTY',
    'UNICODE',
    'SIMPLE',
    'NESTED',
    'HUGE'
]


def test_json(description, method, n):
    output = []

    for case in cases:
        try:
            data, count = globals()[case]
            if case != "HUGE":
                Log.note("{{description}} {{type}}: {{json}}", {
                    "description": description,
                    "type": case,
                    "json": method(data)
                })
        except Exception, e:
            Log.warning("problem with encoding: {{message}}", {"message": e.message}, e)

    for case in cases:
        try:
            data, count = globals()[case]
            t0 = time.time()
            for i in range(n):
                for i in range(count):
                    output.append(method(data))
            duration = time.time() - t0
            Log.note("{{description}} {{type}} x {{num}} x {{count}} = {{time}}", {
                "description": description,
                "time": duration,
                "type": case,
                "num": n,
                "count": globals()[case][1],
                "length": len(output)
            })
        except Exception, e:
            Log.warning("problem with encoding: {{message}}", {"message": e.message}, e)


class EnhancedJSONEncoder(json.JSONEncoder):
    """
    NEEDED TO HANDLE MORE DIVERSE SET OF TYPES
    PREVENTS NATIVE C VERSION FROM RUNNING
    """

    def __init__(self):
        json.JSONEncoder.__init__(self, sort_keys=True)

    def default(self, obj):
        if obj == Null:
            return None
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def main(num):
    try:
        Log.start()
        test_json("util.jsons.json_encoder", json_encoder.encode, num)
        test_json("scrub-then-encode", cPythonJSONEncoder().encode, num)
        test_json("python json.dumps", EnhancedJSONEncoder().encode, num)
        test_json("default json.dumps", json.dumps, num)  #WILL CRASH, CAN NOT HANDLE DIVERSITY OF TYPES
    finally:
        Log.stop()


if __name__ == "__main__":
    main(1)
