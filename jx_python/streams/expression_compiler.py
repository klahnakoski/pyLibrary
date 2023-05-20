# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import Data, is_data, leaves_to_data
from mo_logs import Log, strings, logger
from mo_times.dates import Date

from jx_base.expressions.python_script import PythonScript
from mo_json.typed_object import TypedObject
from mo_future import first
from mo_imports import export

GLOBALS = {
    "Date": Date,
    "logger": logger,
    "Data": Data,
    "leaves_to_data": leaves_to_data,
    "is_data": is_data,
    "first": first,
    "TypedObject": TypedObject,
}


def compile_expression(code: PythonScript, function_name="output"):
    """
    THIS FUNCTION IS ON ITS OWN FOR MINIMAL GLOBAL NAMESPACE

    :param code:  PYTHON SOURCE CODE
    :param function_name:  OPTIONAL NAME TO GIVE TO OUTPUT FUNCTION
    :return:  PYTHON FUNCTION
    """

    fake_globals = {**GLOBALS, **code.locals}
    fake_locals = {}
    loop_depth = 0
    try:
        exec(
            (
                f"def {function_name}(row{loop_depth}, rownum{loop_depth}=None, rows{loop_depth}=None):\n"
                + f"    if not isinstance(row{loop_depth}, TypedObject):\n"
                + f"        logger.warning('Expecting TypedObject')\n"
                + f"        logger.error('Expecting TypedObject')\n"
                + f"    _source = {strings.quote(code.source)}\n"
                + f"    try:\n"
                + f"        return {code.source}\n"
                + f"    except Exception as e:\n"
                + "        logger.error('Problem with dynamic function {{func|quote}}', func=_source, cause=e)\n"
            ),
            fake_globals,
            fake_locals,
        )
        func = fake_locals[function_name]
        setattr(func, "_source", code.source)
        return func
    except Exception as e:
        raise Log.error("Bad source: {{source}}", source=code.source, cause=e)


export("jx_python.expressions._utils", compile_expression)
