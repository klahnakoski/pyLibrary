################################################################################
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this file,
## You can obtain one at http://mozilla.org/MPL/2.0/.
################################################################################
## Author: Kyle Lahnakoski (kyle@lahnakoski.com)
################################################################################


#DUE TO MY POOR MEMORY, THIS IS A LIST OF ALL CONVERSION ROUTINES
import StringIO
import json
import re
import string
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
    def JSON2object(json_string, params=None, flexible=False):
        try:
            #REMOVE """COMMENTS""", #COMMENTS, //COMMENTS, AND \n
            if flexible: json_string=re.sub(r"\"\"\".*?\"\"\"|^\s*//\n|#.*?\n|\n", r" ", json_string)  #DERIVED FROM https://github.com/jeads/datasource/blob/master/datasource/bases/BaseHub.py#L58

            if params is not None:
                params=dict([(k,CNV.value2quote(v)) for k,v in params.items()])
                json_string= string.Template(json_string).substitute(params)

            obj=json.loads(json_string)
            if isinstance(obj, list): return MapList(obj)
            return Map(**obj)
        except Exception, e:
            D.error("Can not decode JSON:\n\t"+json_string, e)


    @staticmethod
    def string2datetime(value, format):
        ## http://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior
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
    def datetime2unixmilli(d):
        return int(time.mktime(d.timetuple())*1000)

    @staticmethod
    def unix2datetime(u):
        return datetime.datetime.fromtimestamp(u)

    @staticmethod
    def unixmilli2datetime(u):
        return datetime.datetime.fromtimestamp(u/1000)



    @staticmethod
    def table2list(
        column_names, #tuple of columns names
        rows          #list of tuples
    ):
        return MapList([dict(zip(column_names, r)) for r in rows])


    #RETURN PRETTY PYTHON CODE FOR THE SAME
    @staticmethod
    def value2quote(value):
        if isinstance(value, basestring):
            return "\""+value.replace("\"", "\\\"")+"\""
        else:
            return repr(value)

    #RETURN PYTHON CODE FOR THE SAME
    @staticmethod
    def value2code(value):
        return repr(value)


    @staticmethod
    def DataFrame2string(df, columns=None):
        output = StringIO.StringIO()
        try:
            df.to_csv(output, sep="\t", header=True, cols=columns, engine='python')
            return output.getvalue()
        finally:
            output.close()

    @staticmethod
    def ascii2char(ascii):
        return chr(ascii)

    @staticmethod
    def char2ascii(char):
        return ord(char)

    @staticmethod
    def int2hex(value, size):
        return (("0"*size)+hex(value)[2:])[-size:]