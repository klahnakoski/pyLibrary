#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####


#DUE TO MY POOR MEMORY, THIS IS A LIST OF ALL CONVERSION ROUTINES
import json
import time
import datetime
from util.map import Map

class CNV:

    @staticmethod
    def object2JSON(obj):
        return json.dumps(obj)

    @staticmethod
    def JSON2object(json_string):
        return Map(**json.loads(json_string))



    @staticmethod
    def datetime2unix(cls, d):
        return time.mktime(d.timetuple())

    @staticmethod
    def unix2datetime(cls, u):
        return datetime.datetime.fromtimestamp(u)


    @staticmethod
    def table2list(
        column_names, #tuple of columns names
        rows          #list of tuples
    ):
        return [Map(**dict(zip(column_names, r))) for r in rows]
