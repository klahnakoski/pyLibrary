################################################################################
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this file,
## You can obtain one at http://mozilla.org/MPL/2.0/.
################################################################################
## Author: Kyle Lahnakoski (kyle@lahnakoski.com)
################################################################################
import re
from string import _TemplateMetaclass


def indent(value, prefix=None):
    if prefix is None: prefix="\t"
    return prefix+("\n"+prefix).join(value.rstrip().splitlines())


def outdent(value):
    num=100
    lines=value.splitlines()
    for l in lines:
        trim=len(l.lstrip())
        if trim>0: num=min(num, len(l)-len(l.lstrip()))
    return "\n".join([l[num:] for l in lines])

def between(value, prefix, suffix):
    s = value.find(prefix)
    if s==-1: return None
    s+=len(prefix)

    e=value.find(suffix, s)
    if e==-1: raise Exception("can not find '"+suffix+"'")

    s=value.rfind(prefix, 0, e)+len(prefix) #WE KNOW THIS EXISTS, BUT THERE MAY BE A RIGHT-MORE ONE
    return value[s:e]


def right(value, len):
    if len<=0: return ""
    return value[-len:]

def find_first(value, find_arr, start=0):
    i=len(value)
    for f in find_arr:
        temp=value.find(f, start)
        if temp==-1: continue
        i=min(i, temp)
    if i==len(value): return -1
    return i

