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

else:
    import __builtin__

    text_type = __builtin__.unicode
    binary_type = str
    long = __builtin__.long
    xrange = __builtin__.xrange

