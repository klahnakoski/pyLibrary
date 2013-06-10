#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####


#from string import Template
from string import Template
import sys

#for debugging (do I even want an object in Python? - at least these methods
# are easily searchable, keep it for now)
import traceback
from util.strings import indent

class D(object):

    @staticmethod
    def println(template, params=None):
        if params is None:
            sys.stdout.write(template+"\n")
        else:
            sys.stdout.write(Template(template).safe_substitute(params)+"\n")

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

        raise Except(template, params, cause, format_trace(traceback.extract_stack(), 1+offset))





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