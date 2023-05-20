from mo_logs import logger

from jx_base import jx_expression
from jx_base.expressions import (
    Expression,
    Variable,
    GetOp,
    EqOp,
    Literal,
    AndOp,
    OrOp,
    NeOp,
    CallOp,
    LastOp,
    FirstOp,
    ModOp,
    LtOp,
    GtOp,
    LteOp,
    GteOp,
    NULL,
    FALSE,
    TRUE,
    NameOp,
    AddOp,
    SubOp,
    DivOp,
    MulOp,
    NotOp,
    ToArrayOp,
)
from jx_python.expressions import Python, PythonFunction
from jx_python.streams.expression_compiler import compile_expression
from jx_python.streams.inspects import is_function
from jx_python.streams.typers import Typer
from mo_json import JX_ANY

Any = Typer(python_type=JX_ANY)


class ExpressionFactory:
    """
    USE PYTHON MAGIC METHODS TO BUILD EXPRESSIONS
    """

    def __init__(self, expr):
        self.expr: Expression = expr

    def build(self):
        return compile_expression(self.expr.partial_eval(Python).to_python(0))

    def first(self):
        return ExpressionFactory(FirstOp(self.expr))

    def last(self):
        return ExpressionFactory(LastOp(self.expr))

    def to_list(self):
        return ExpressionFactory(ToArrayOp(self.expr))

    def to_value(self):
        return ExpressionFactory(ToValueOp(self.expr))

    def sum(self):
        return ExpressionFactory(AddOp(self.expr, nulls=True))

    def __getattr__(self, item):
        return ExpressionFactory(GetOp(self.expr, Literal(item)))

    def __call__(self, *args, **kwargs):
        args = [factory(a).build() for a in args]
        kwargs = {k: factory(v).build() for k, v in kwargs.items()}
        return ExpressionFactory(CallOp(self.expr, *args, **kwargs))

    def __add__(self, other):
        other = factory(other)
        return ExpressionFactory(AddOp(self.expr, other.expr))

    def __sub__(self, other):
        other = factory(other)
        return ExpressionFactory(SubOp(self.expr, other.expr))

    def __mul__(self, other):
        other = factory(other)
        return ExpressionFactory(MulOp(self.expr, other.expr))

    def __truediv__(self, other):
        other = factory(other)
        return ExpressionFactory(DivOp(self.expr, other.expr))

    def __eq__(self, other):
        other = factory(other)
        return ExpressionFactory(EqOp(self.expr, other.expr))

    def __ne__(self, other):
        other = factory(other)
        return ExpressionFactory(NeOp(self.expr, other.expr))

    def __and__(self, other):
        other = factory(other)
        return ExpressionFactory(AndOp(self.expr, other.expr))

    def __or__(self, other):
        other = factory(other)
        return ExpressionFactory(OrOp(self.expr, other.expr))

    def __not__(self):
        return ExpressionFactory(NotOp(self.expr))

    def __mod__(self, other):
        other = factory(other)
        return ExpressionFactory(ModOp(self.expr, other.expr))

    def __lt__(self, other):
        other = factory(other)
        return ExpressionFactory(LtOp(self.expr, other.expr))

    def __le__(self, other):
        other = factory(other)
        return ExpressionFactory(LteOp(self.expr, other.expr))

    def __ge__(self, other):
        other = factory(other)
        return ExpressionFactory(GteOp(self.expr, other.expr))

    def __gt__(self, other):
        other = factory(other)
        return ExpressionFactory(GtOp(self.expr, other.expr))

    def __rshift__(self, other):
        if not isinstance(other, str):
            logger.error("expecting string")
        return ExpressionFactory(NameOp(self.expr, Literal(other)))

    def __rlshift__(self, other):
        if not isinstance(other, str):
            logger.error("expecting string")
        return ExpressionFactory(NameOp(self.expr, Literal(other)))

    def __data__(self):
        return str(self.expr)


def factory(expr) -> ExpressionFactory:
    """
    assemble the expression
    """

    if expr is None:
        return ExpressionFactory(NULL)
    if expr is True:
        return ExpressionFactory(TRUE)
    if expr is False:
        return ExpressionFactory(FALSE)
    if isinstance(expr, ExpressionFactory):
        return expr

    if is_function(expr):
        return ExpressionFactory(PythonFunction(expr))

    if not isinstance(expr, Expression):
        expr = jx_expression(expr)

    if expr.op == Literal.op:
        return ExpressionFactory(expr)

    return ExpressionFactory(expr)


class TopExpressionFactory(ExpressionFactory):
    """
    it(x)  RETURNS A FunctionFactory FOR x
    """

    def __call__(self, value):
        # much like an import of a value
        if isinstance(value, ExpressionFactory):
            logger.error("don't do this")

        return ExpressionFactory(PythonFunction(lambda: value))

    def __str__(self):
        return "it"


it = TopExpressionFactory(Variable("."))
