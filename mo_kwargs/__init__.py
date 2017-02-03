# encoding: utf-8
#
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

from collections import Mapping

from mo_dots import zip as dict_zip


def override(func):
    """
    THIS DECORATOR WILL PUT ALL PARAMETERS INTO THE `settings` PARAMETER AND
    PUT ALL `settings` PARAMETERS INTO THE FUNCTION PARAMETERS.  THIS HAS BOTH
    THE BENEFIT OF HAVING ALL PARAMETERS IN ONE PLACE (settings) AND ALL
    PARAMETERS ARE EXPLICIT FOR CLARITY.

    OF COURSE, THIS MEANS PARAMETER ASSIGNMENT MAY NOT BE UNIQUE: VALUES CAN
    COME FROM EXPLICIT CALL PARAMETERS, OR FROM THE settings PARAMETER.  IN
    THESE CASES, PARAMETER VALUES ARE CHOSEN IN THE FOLLOWING ORDER:
    1) EXPLICT CALL PARAMETERS
    2) PARAMETERS FOUND IN settings
    3) DEFAULT VALUES ASSIGNED IN FUNCTION DEFINITION
    """

    params = func.func_code.co_varnames[:func.func_code.co_argcount]
    if not func.func_defaults:
        defaults = {}
    else:
        defaults = {k: v for k, v in zip(reversed(params), reversed(func.func_defaults))}

    if "settings" not in params:
        # WE ASSUME WE ARE ONLY ADDING A settings PARAMETER TO SOME REGULAR METHOD
        def w_settings(*args, **kwargs):
            settings = kwargs.get("settings")

            params = func.func_code.co_varnames[:func.func_code.co_argcount]
            if not func.func_defaults:
                defaults = {}
            else:
                defaults = {k: v for k, v in zip(reversed(params), reversed(func.func_defaults))}

            ordered_params = dict(zip(params, args))

            return func(**params_pack(params, ordered_params, kwargs, settings, defaults))
        return w_settings

    def wrapper(*args, **kwargs):
        try:
            if func.func_name in ("__init__", "__new__") and "settings" in kwargs:
                packed = params_pack(params, kwargs, dict_zip(params[1:], args[1:]), kwargs["settings"], defaults)
                return func(args[0], **packed)
            elif func.func_name in ("__init__", "__new__") and len(args) == 2 and len(kwargs) == 0 and isinstance(args[1], Mapping):
                # ASSUME SECOND UNNAMED PARAM IS settings
                packed = params_pack(params, args[1], defaults)
                return func(args[0], **packed)
            elif func.func_name in ("__init__", "__new__"):
                # DO NOT INCLUDE self IN SETTINGS
                packed = params_pack(params, kwargs, dict_zip(params[1:], args[1:]), defaults)
                return func(args[0], **packed)
            elif params[0] == "self" and "settings" in kwargs:
                packed = params_pack(params, kwargs, dict_zip(params[1:], args[1:]), kwargs["settings"], defaults)
                return func(args[0], **packed)
            elif params[0] == "self" and len(args) == 2 and len(kwargs) == 0 and isinstance(args[1], Mapping):
                # ASSUME SECOND UNNAMED PARAM IS settings
                packed = params_pack(params, args[1], defaults)
                return func(args[0], **packed)
            elif params[0] == "self":
                packed = params_pack(params, kwargs, dict_zip(params[1:], args[1:]), defaults)
                return func(args[0], **packed)
            elif len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], Mapping):
                # ASSUME SINGLE PARAMETER IS A SETTING
                packed = params_pack(params, args[0], defaults)
                return func(**packed)
            elif "settings" in kwargs and isinstance(kwargs["settings"], Mapping):
                # PUT args INTO SETTINGS
                packed = params_pack(params, kwargs, dict_zip(params, args), kwargs["settings"], defaults)
                return func(**packed)
            else:
                # PULL SETTINGS OUT INTO PARAMS
                packed = params_pack(params, kwargs, dict_zip(params, args), defaults)
                return func(**packed)
        except TypeError, e:
            from mo_logs import Log
            if e.message.find("takes at least") >= 0:
                missing = [p for p in params if str(p) not in packed]
                Log.error(
                    "Problem calling {{func_name}}:  Expecting parameter {{missing}}",
                    func_name=func.func_name,
                    missing=missing,
                    stack_depth=1
                )
            Log.error("Unexpected", e)
    return wrapper


def params_pack(params, *args):
    settings = {}
    for a in args:
        for k, v in a.items():
            k = unicode(k)
            if k in settings:
                continue
            settings[k] = v
    settings["settings"] = settings

    output = {str(k): settings[k] for k in params if k in settings}
    return output
