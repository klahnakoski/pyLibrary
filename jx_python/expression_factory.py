from jx_base import jx_expression
from jx_base.expressions import Expression, Variable, GetOp, EqOp, Literal
from jx_python.expression_compiler import compile_expression
from jx_python.expressions import Python
from mo_logs import logger
from mo_streams import Typer
from mo_streams.type_utils import JxTyper, UnknownTyper, LazyTyper


class ExpressionFactory:
    def __init__(self, expr, domain):
        self.expr: Expression = expr
        self.domain: Typer = domain or LazyTyper()

    def build(self):
        return compile_expression(
            self.expr.partial_eval(Python).to_python(), "some_function"
        )

    def __getattr__(self, item):
        item_type = getattr(self.domain, item)

        return ExpressionFactory(GetOp(self.expr, factory(item).expr), item_type)

    def __eq__(self, other):
        other = factory(other)
        return ExpressionFactory(EqOp(self, other), Typer(python_type=bool))

    def to_list(self):
        self.build()(None)


def factory(expr, typer=None) -> ExpressionFactory:
    """
    assemble the expression
    """
    if isinstance(expr, ExpressionFactory):
        return ExpressionFactory(expr.expr, typer)

    if not isinstance(expr, Expression):
        expr = jx_expression(expr)

    return ExpressionFactory(expr, typer)


class TopExpressionFactory(ExpressionFactory):
    """
    it(x)  RETURNS A FunctionFactory FOR x
    """

    def __call__(self, value):
        # much like an import of a value
        if isinstance(value, ExpressionFactory):
            logger.error("don't do this")

        return ExpressionFactory(
            Literal("."), Typer(python_type=type(value)), f"{value}"
        )

    def __str__(self):
        return "it"


it = TopExpressionFactory(Variable("."), UnknownTyper(Exception("unknonwn type")))
