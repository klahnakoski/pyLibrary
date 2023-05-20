# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from dataclasses import dataclass
from typing import Any, Dict

from mo_dots import is_data, is_list, Null
from mo_future import is_text, extend
from mo_imports import expect
from mo_logs import strings

from jx_python.utils import merge_locals
from mo_json.types import JX_BOOLEAN, JX_IS_NULL, JX_NUMBER

from jx_base.expressions import FALSE, NULL, NullOp, jx_expression, PythonScript, TRUE
from jx_base.language import Language, is_expression, is_op

ToNumberOp, OrOp, ScriptOp, WhenOp, compile_expression = expect(
    "ToNumberOp", "OrOp", "ScriptOp", "WhenOp", "compile_expression"
)


def jx_expression_to_function(expr):
    """
    RETURN FUNCTION THAT REQUIRES PARAMETERS (row, rownum=None, rows=None):
    """
    if expr == None:
        return Null

    if is_expression(expr):
        # ALREADY AN EXPRESSION OBJECT
        if is_op(expr, ScriptOp) and not is_text(expr.script):
            return expr.script
        else:
            func = compile_expression(expr.to_python())
            return JXExpression(func, expr.__data__())
    if not is_data(expr) and not is_list(expr) and hasattr(expr, "__call__"):
        # THIS APPEARS TO BE A FUNCTION ALREADY
        return expr

    expr = jx_expression(expr)
    func = compile_expression((expr).to_python())
    return JXExpression(func, expr)


class JXExpression(object):
    def __init__(self, func, expr):
        self.func = func
        self.expr = expr

    def __call__(self, *args, **kwargs):
        return self.func(*args)

    def __str__(self):
        return str(self.expr.__data__())

    def __repr__(self):
        return repr(self.expr.__data__())

    def __data__(self):
        return self.expr.__data__()


@extend(NullOp)
def to_python(self, loop_depth=0):
    return PythonScript({}, loop_depth, JX_IS_NULL, "None", NullOp, TRUE)


def _inequality_to_python(self, loop_depth=0):
    op, identity = _python_operators[self.op]
    lhs = ToNumberOp(self.lhs).partial_eval(Python).to_python(loop_depth)
    rhs = ToNumberOp(self.rhs).partial_eval(Python).to_python(loop_depth)
    script = f"({lhs.source}) {op} ({rhs.source})"

    return (
        WhenOp(
            OrOp(self.lhs.missing(Python), self.rhs.missing(Python)),
            **{
                "then": FALSE,
                "else": PythonScript({**lhs.locals, **rhs.locals}, loop_depth, JX_BOOLEAN, script, self),
            },
        )
        .partial_eval(Python)
        .to_python(loop_depth)
    )


def _binaryop_to_python(self, loop_depth, not_null=False, boolean=False):
    op, identity = _python_operators[self.op]

    lhs = ToNumberOp(self.lhs).partial_eval(Python).to_python(loop_depth)
    rhs = ToNumberOp(self.rhs).partial_eval(Python).to_python(loop_depth)
    script = f"({lhs.source}){op}({rhs.source})"
    missing = OrOp(lhs.missing(Python), rhs.missing(Python)).partial_eval(Python)
    return PythonScript(merge_locals(lhs.locals, rhs.locals), loop_depth, JX_NUMBER, script, self, missing)


def multiop_to_python(self, loop_depth):
    sign, zero = _python_operators[self.op]
    if len(self.terms) == 0:
        return (self.default).to_python(loop_depth)
    elif self.default is NULL:
        return sign.join("coalesce(" + t.to_python(loop_depth) + ", " + zero + ")" for t in self.terms)
    else:
        return (
            "coalesce("
            + sign.join("(" + t.to_python(loop_depth) + ")" for t in self.terms)
            + ", "
            + self.default.to_python(loop_depth)
            + ")"
        )


def with_var(var, expression, eval):
    """
    :param var: NAME GIVEN TO expression
    :param expression: THE EXPRESSION TO COMPUTE FIRST
    :param eval: THE EXPRESSION TO COMPUTE SECOND, WITH var ASSIGNED
    :return: PYTHON EXPRESSION
    """
    return "[(" + eval + ") for " + var + " in [" + expression + "]][0]"


Python = Language("Python")


@dataclass
class PythonSource:
    locals: Dict[str, Any]
    source: str

    def __str__(self):
        return self.source

    def __data__(self):
        return strings.quote(self.source)


_python_operators = {
    "add": (" + ", "0"),  # (operator, zero-array default value) PAIR
    "sum": (" + ", "0"),
    "mul": (" * ", "1"),
    "sub": (" - ", None),
    "div": (" / ", None),
    "exp": (" ** ", None),
    "mod": (" % ", None),
    "gt": (" > ", None),
    "gte": (" >= ", None),
    "lte": (" <= ", None),
    "lt": (" < ", None),
}
