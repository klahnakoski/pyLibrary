# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import inspect

from mo_logs import logger


def is_function(value):
    if type(value).__name__ == "function":
        return True
    if isinstance(value, type):
        return True
    if hasattr(value, "__call__"):
        logger.error("not expected")
    return False


def arg_spec(type_, item):
    for name, func in inspect.getmembers(type_):
        if name != item:
            continue
        return inspect.getfullargspec(func)
