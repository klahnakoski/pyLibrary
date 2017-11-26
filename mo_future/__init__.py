# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2

NoneType = type(None)


if PY3:
    text_type = str
    binary_type = bytes
    long = int
    xrange = range
    round = round
    from html.parser import HTMLParser
    from urllib.parse import urlparse
    from io import StringIO
    from _thread import allocate_lock, get_ident

else:
    import __builtin__

    text_type = __builtin__.unicode
    binary_type = str
    long = __builtin__.long
    xrange = __builtin__.xrange
    round = __builtin__.round
    import HTMLParser
    from urlparse import urlparse
    import StringIO
    from thread import allocate_lock, get_ident



# class python2(object):
#     def __init__(self, name):
#         self.name = name
#
#     def __call__(self, func):
#         if PY2:
#             setattr(clazz, self.name, func)
#         return func


def python2(func):
    if PY2:
        return func


def python3(func):
    if PY3:
        return func

# class python3(object):
#     def __init__(self, name):
#         self.name = name
#
#     def __call__(self, func):
#         if PY3:
#             import inspect
#             if inspect.ismethod(func):
#                 for cls in inspect.getmro(func.__self__.__class__):
#                    if cls.__dict__.get(func.__name__) is func:
#                         return cls
#                 func = func.__func__  # fallback
#
#
#             setattr(clazz, self.name, func)
#         return func
#
