################################################################################
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this file,
## You can obtain one at http://mozilla.org/MPL/2.0/.
################################################################################
## Author: Kyle Lahnakoski (kyle@lahnakoski.com)
################################################################################


#from string import Template
from datetime import datetime
import inspect
from logging import LogRecord
from string import Template
import sys

#for debugging (do I even want an object in Python? - at least these methods
# are easily searchable, keep it for now)
import threading
import traceback
import logging
from util.strings import indent
from util.map import Map, MapList
import util
from util.files import File


class D(object):


    @classmethod
    def add_log(cls, log):
        cls.logs.append(log)


    @staticmethod
    def println(template, params=None):
        if not isinstance(template, Template): template=Template("${log_timestamp} - "+template)
        if params is None: params={}

        #NICE TO GATHER MANY MORE ITEMS FOR LOGGING (LIKE STACK TRACES AND LINE NUMBERS)
        params["log_timestamp"]=datetime.utcnow().strftime("%H:%M:%S")

        for l in D.logs:
            l.println(template, params)

    @staticmethod
    def warning(template, params=None, cause=None):
        if isinstance(params, BaseException):
            cause=params
            params=None

        if not isinstance(cause, Except):
            cause=Except(str(cause), trace=format_trace(traceback.extract_tb(sys.exc_info()[2]), 0))

        e = Except(template, params, cause, format_trace(traceback.extract_stack(), 1))
        D.println(str(e))

    #raise an exception with a trace for the cause too
    @staticmethod
    def error(
        template,       #human readable template
        params=None,    #parameters for template
        cause=None,     #pausible cause
        offset=0        #stack trace offset (==1 if you do not want to report self)
    ):
        if isinstance(params, BaseException):
            cause=params
            params=None

        if not isinstance(cause, Except):
            cause=Except(str(cause), trace=format_trace(traceback.extract_tb(sys.exc_info()[2]), offset))

        trace=format_trace(traceback.extract_stack(), 1+offset)
        e=Except(template, params, cause, trace)
        raise e


    @staticmethod
    def settings(settings):
        ##http://victorlin.me/2012/08/good-logging-practice-in-python/
        if settings is None: return
        if settings.log is None: return

        if not isinstance(settings.log, MapList): settings.log=[settings.log]
        for log in settings.log:
            D.add_log(Log.new_instance(log))

            


D.info=D.println


def format_trace(tbs, trim=0):
    tbs.reverse()
    list = []
    for filename, lineno, name, line in tbs[trim:]:
        item = 'at %s:%d (%s)\n' % (filename,lineno,name)
        list.append(item)
    return "".join(list)


#def format_trace(tb, trim=0):
#    list = []
#    for filename, lineno, name, line in traceback.extract_tb(tb)[0:-trim]:
#        item = 'File "%s", line %d, in %s\n' % (filename,lineno,name)
#        if line:
#            item = item + '\t%s\n' % line.strip()
#        list.append(item)
#    return "".join(list)





class Except(Exception):
    def __init__(self, template=None, params=None, cause=None, trace=None):
        super(Exception, self).__init__(self)
        self.template=template
        self.params=params
        self.cause=cause
        self.trace=trace

    @property
    def message(self):
        return str(self)

    def __str__(self):
        output=self.template
        if self.params is not None: output=Template(output).safe_substitute(self.params)

        if self.trace is not None:
            output+="\n"+indent(self.trace)

        if self.cause is not None:
            output+="\ncaused by\n\t"+self.cause.__str__()

        return output+"\n"





class Log():
    @classmethod
    def new_instance(cls, settings):
        settings=util.map.wrap(settings)
        if settings["class"] is not None: return Log_usingLogger(settings)
        if settings.file is not None: return Log_usingFile(file)
        if settings.filename is not None: return Log_usingFile(settings.filename)
        if settings.stream is not None: return Log_usingStream(settings.stream)


        

class Log_usingFile():

    def __init__(self, file):
        assert file is not None
        self.file_name=file
        self.file_lock=threading.Lock()


    def println(self, template, params):
        with self.file_lock:
            File(self.filename).append(template.substitute(params))




class Log_usingLogger():
    def __init__(self, settings):
        assert settings["class"] is not None
        self.logger=logging.Logger("unique name", level=logging.INFO)


        # IMPORT MODULE FOR HANDLER
        path=settings["class"].split(".")
        class_name=path[-1]
        path=".".join(path[:-1])
        temp=__import__(path, globals(), locals(), [class_name], -1)
        constructor=object.__getattribute__(temp, class_name)

        params = settings.dict
        del params['class']
        self.logger.addHandler(constructor(**params))

    def println(self, template, params):
        # http://docs.python.org/2/library/logging.html#logging.LogRecord
        self.logger.info(template.substitute(params))


            
class Log_usingStream():

    def __init__(self, stream):
        assert stream is not None
        self.stream=stream


    def println(self, template, params):
        try:
            self.stream.write(template.substitute(params)+"\n")
        except Exception, e:
            pass





D.logs=[Log.new_instance({"stream":sys.stdout})]

