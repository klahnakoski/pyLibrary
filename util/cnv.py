################################################################################
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this file,
## You can obtain one at http://mozilla.org/MPL/2.0/.
################################################################################
## Author: Kyle Lahnakoski (kyle@lahnakoski.com)
################################################################################


#DUE TO MY POOR MEMORY, THIS IS A LIST OF ALL CONVERSION ROUTINES
import json
import re
import time
import datetime
from util.debug import D
from util.map import Map, MapList

class CNV:

    @staticmethod
    def object2JSON(obj):
        if isinstance(obj, Map):
            return json.dumps(obj.dict)
        return json.dumps(obj)

    @staticmethod
    def JSON2object(json_string, flexible=False):
        #REMOVE """COMMENTS""", #COMMENTS, //COMMENTS, AND \n
        if flexible: json_string=re.sub(r"\"\"\".*?\"\"\"|^\s*//\n|#.*?\n|\n", r" ", json_string)  #DERIVED FROM https://github.com/jeads/datasource/blob/master/datasource/bases/BaseHub.py#L58
        obj=json.loads(json_string)
        if isinstance(obj, list): return MapList(obj)
        return Map(**obj)

    @staticmethod
    def string2datetime(value, format):
        try:
            return datetime.datetime.strptime(value, format)
        except Exception, e:
            D.error("Can not format ${value} with ${format}", {"value":value, "format":format}, e)


    @staticmethod
    def datetime2string(value, format):
        try:
            return value.strftime(format)
        except Exception, e:
            D.error("Can not format ${value} with ${format}", {"value":value, "format":format}, e)



    @staticmethod
    def datetime2unix(d):
        return time.mktime(d.timetuple())

    @staticmethod
    def unix2datetime(u):
        return datetime.datetime.fromtimestamp(u)


    @staticmethod
    def table2list(
        column_names, #tuple of columns names
        rows          #list of tuples
    ):
        return [Map(**dict(zip(column_names, r))) for r in rows]
