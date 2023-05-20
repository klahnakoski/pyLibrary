# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_imports import export, expect

from mo_streams.type_utils import CallableTyper

Typer = expect("Typer")


def parse(type_desc):
    """
    THIS FUNCTION IS INCOMPLETE
    """
    if isinstance(type_desc, type):
        # SOME TYPE ANNOTATIONS ARE ACTUAL TYPES, NOT STRINGS
        return CallableTyper(return_type=type_desc)

    types = [clean for t in type_desc.split("|") for clean in [t.strip()] if clean != "None"]

    if len(types) == 1:
        if types[0] == "str":
            return CallableTyper(return_type=str)

    raise NotImplementedError()


export("mo_streams.type_utils", parse)
