# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import inspect
from collections import namedtuple
from types import FunctionType

from mo_dots import is_missing
from mo_logs import logger, Except, strings
from mo_logs.exceptions import ERROR, get_stacktrace

from mo_streams.type_utils import Typer, LazyTyper, CallableTyper, UnknownTyper

DEBUG = False

_get = object.__getattribute__
_set = object.__setattr__

BuiltFunction = namedtuple("BuiltFunction", ["function", "return_type", "schema"])
NO_ARGS = BuiltFunction(tuple(), tuple(), tuple())


class FunctionFactory:
    """
    See mo-streams/docs/function_factory.md
    """

    def __init__(self, builder, typer, desc):
        if not isinstance(typer, Typer):
            logger.error("expecting type, not {{type}}", type=typer)
        _set(self, "build", builder)
        _set(self, "typer", typer)
        _set(self, "_desc", desc)

    def __getattr__(self, item):
        source = f"{self}.{item}"

        def builder(domain_type, domain_schema) -> BuiltFunction:
            f, t, s = _get(self, "build")(domain_type, domain_schema)
            if item in s:

                def get_schema_item(v, a):
                    try:
                        return a[item]
                    finally:
                        DEBUG and logger.info("run {{source}}", source=source)

                return BuiltFunction(get_schema_item, domain_schema[item], domain_schema)
            elif isinstance(item, FunctionFactory):
                f, t, s = item.build(domain_type, domain_schema)

                def get_func_item(v, a):
                    try:
                        return getattr(f(v, a), f(v, a))
                    finally:
                        DEBUG and logger.info("run {{source}}", source=source)

                return BuiltFunction(get_func_item, UnknownTyper(Exception("too complicated to know type")), s)
            else:

                def get_const_item(v, a):
                    try:
                        return getattr(f(v, a), item)
                    finally:
                        DEBUG and logger.info("run {{source}}", source=source)

                return BuiltFunction(get_const_item, getattr(t, item), s)

        return FunctionFactory(builder, getattr(_get(self, "typer"), item), source)

    def __eq__(self, other):
        func_other = factory(other)

        def builder(domain_type, domain_schema) -> BuiltFunction:
            sf, st, ss = self.build(domain_type, domain_schema)
            of, ot, os = func_other.build(domain_type, domain_schema)

            def func(v, a):
                return sf(v, a) == of(v, a)

            return BuiltFunction(func, Typer(python_type=bool), domain_schema)

        return FunctionFactory(builder, Typer(python_type=bool), f"{other} == {self}")

    def __gt__(self, other):
        func_other = factory(other)

        def builder(domain_type, domain_schema) -> BuiltFunction:
            sf, st, ss = self.build(domain_type, domain_schema)
            of, ot, os = func_other.build(domain_type, domain_schema)

            def func(v, a):
                return sf(v, a) > of(v, a)

            return BuiltFunction(func, Typer(python_type=bool), domain_schema)

        return FunctionFactory(builder, Typer(python_type=bool), f"{other} > {self}")

    def __ge__(self, other):
        func_other = factory(other)

        def builder(domain_type, domain_schema) -> BuiltFunction:
            sf, st, ss = self.build(domain_type, domain_schema)
            of, ot, os = func_other.build(domain_type, domain_schema)

            def func(v, a):
                return sf(v, a) >= of(v, a)

            return BuiltFunction(func, Typer(python_type=bool), domain_schema)

        return FunctionFactory(builder, Typer(python_type=bool), f"{other} >= {self}")

    def __lt__(self, other):
        func_other = factory(other)

        def builder(domain_type, domain_schema) -> BuiltFunction:
            sf, st, ss = self.build(domain_type, domain_schema)
            of, ot, os = func_other.build(domain_type, domain_schema)

            def func(v, a):
                return sf(v, a) < of(v, a)

            return BuiltFunction(func, Typer(python_type=bool), domain_schema)

        return FunctionFactory(builder, Typer(python_type=bool), f"{other} < {self}")

    def __le__(self, other):
        func_other = factory(other)

        def builder(domain_type, domain_schema) -> BuiltFunction:
            sf, st, ss = self.build(domain_type, domain_schema)
            of, ot, os = func_other.build(domain_type, domain_schema)

            def func(v, a):
                return sf(v, a) <= of(v, a)

            return BuiltFunction(func, Typer(python_type=bool), domain_schema)

        return FunctionFactory(builder, Typer(python_type=bool), f"{other} <= {self}")

    def __truediv__(self, other):
        func_other = factory(other)

        def builder(domain_type, domain_schema) -> BuiltFunction:
            sf, st, ss = self.build(domain_type, domain_schema)
            of, ot, os = func_other.build(domain_type, domain_schema)

            def func(v, a):
                sv = sf(v, a)
                ov = of(v, a)
                if is_missing(sv) or is_missing(ov):
                    return None
                return sv / ov

            return BuiltFunction(func, Typer(python_type=float), domain_schema)

        return FunctionFactory(builder, Typer(python_type=float), f"{other} / {self}")

    def __rsub__(self, other):
        func_other = factory(other)

        def builder(domain_type, domain_schema) -> BuiltFunction:
            sf, st, ss = self.build(domain_type, domain_schema)
            of, ot, os = func_other.build(domain_type, domain_schema)

            def func(v, a):
                return of(v, a) - sf(v, a)

            return BuiltFunction(func, st, domain_schema)

        type_ = Typer(example=other) + _get(self, "typer")
        return FunctionFactory(builder, type_, f"{other} - {self}")

    def __radd__(self, other):
        func_other = factory(other)

        def builder(domain_type, domain_schema) -> BuiltFunction:
            sf, st, ss = self.build(domain_type, domain_schema)
            of, ot, os = func_other.build(domain_type, domain_schema)

            def func(v, a):
                return of(v, a) + sf(v, a)

            return BuiltFunction(func, st, domain_schema)

        type_ = Typer(example=other) + _get(self, "typer")
        return FunctionFactory(builder, type_, f"{other} + {self}")

    def __call__(self, *args, **kwargs):
        args = [factory(a) for a in args]
        kwargs = {k: factory(v) for k, v in kwargs.items()}

        desc_args = [str(a) for a in args]
        desc_args.extend(f"{k}={v}" for k, v in kwargs.items())
        params = ",".join(desc_args)
        source = f"{self}({params})"

        def builder(domain_type, domain_schema) -> BuiltFunction:
            sf, st, ss = self.build(domain_type, domain_schema)
            _args = BuiltFunction(*zip(*(a.build(st, ss) for a in args))) if args else NO_ARGS
            _kwargs = {k: v.build(st, ss).function for k, v in kwargs.items()}

            def func(v, a):
                callee = None
                result = None
                try:
                    callee = sf(v, a)
                    call_args = [f(v, a) for f in _args.function]
                    call_kwargs = {k: f(v, a) for k, f in _kwargs.items()}
                    result = callee(*call_args, **call_kwargs)
                    return result
                finally:
                    DEBUG and logger.info(
                        "call {{source}} on {{callee}} result {{result}}", source=source, callee=callee, result=result
                    )

            setattr(func, "source", source)

            return BuiltFunction(func, st(*_args.return_type), domain_schema)

        return FunctionFactory(builder, _get(self, "typer"), source)

    def __str__(self):
        return _get(self, "_desc")


def factory(item, return_type=None):
    if isinstance(item, FunctionFactory):
        return item

    # CONSTANT
    def build_constant(domain_type, domain_schema) -> BuiltFunction:
        return BuiltFunction(lambda v, a: item, Typer(example=item), domain_schema)

    return FunctionFactory(build_constant, Typer(example=item), f"{item}")


def normalize(item, return_type=None):
    """
    RETURN A FUNCTION THAT CAN ACT ON THE value/attachment PAIR FOUND IN STREAMS
    """
    if isinstance(item, FunctionFactory):
        return item

    if isinstance(item, (str, bytes, bool, int, float)):
        # CONSTANT
        def build_constant(domain_type, domain_schema) -> BuiltFunction:
            return BuiltFunction(lambda v, a: item, Typer(example=item), domain_schema)

        return FunctionFactory(build_constant, Typer(example=item), f"{item}")
    else:
        normalized_func, return_type = wrap_func(item, return_type=return_type)

        def builder(domain_type, domain_schema) -> BuiltFunction:
            if isinstance(return_type, LazyTyper):
                return BuiltFunction(normalized_func, domain_type, domain_schema)
            return BuiltFunction(normalized_func, return_type, domain_schema)

        return FunctionFactory(builder, return_type, f"returning {return_type}")


#
# def build(item) -> BuiltFunction:
#     if isinstance(item, FunctionFactory):
#         return item.build
#
#     def builder(domain_type, domain_schema) -> BuiltFunction:
#         return BuiltFunction(lambda v, a: item, Typer(example=item), domain_schema)
#
#     return builder


# build list of single arg builtins, that can be used as parse actions
singleArgBuiltins = [
    sum,
    len,
    sorted,
    reversed,
    list,
    tuple,
    set,
    any,
    all,
    min,
    max,
]

singleArgTypes = [
    int,
    float,
    str,
    bool,
    complex,
    dict,
]


def wrap_func(func, return_type=None):
    try:
        func_name = getattr(func, "__name__", getattr(func, "__class__").__name__)
    except Exception:
        func_name = str(func)
    if func_name.startswith("<"):
        func_name = "func"

    if func in singleArgBuiltins:
        spec = inspect.getfullargspec(func)
    elif func.__class__.__name__ == "staticmethod":
        func = func.__func__
        spec = inspect.getfullargspec(func)
    elif func.__class__.__name__ == "builtin_function_or_method":
        spec = inspect.getfullargspec(func)
    elif func in singleArgTypes:
        spec = inspect.FullArgSpec(["value"], None, None, None, [], None, {})
        return_type = func
    elif isinstance(func, type):
        spec = inspect.getfullargspec(func.__init__)
        new_func = func.__call__
        # USE ONLY FIRST PARAMETER
        num_args = len(spec.args) - 1  # ASSUME self IS FIRST ARG
        if num_args == 0:

            def wrap_init0(val, att):
                return new_func()

            return wrap_init0, Typer(python_type=func)
        else:

            def wrap_init1(val, att):
                return new_func(val)

            return wrap_init1, Typer(python_type=func)
    elif isinstance(func, FunctionType):
        spec = inspect.getfullargspec(func)
    elif hasattr(func, "__call__"):
        spec = inspect.getfullargspec(func)

    if spec.varargs:
        num_args = 3
    elif spec.args and spec.args[0] in ["cls", "self"]:
        num_args = len(spec.args) - 1
    else:
        num_args = len(spec.args)

    if not return_type:
        return_type = spec.annotations.get("return")
    if return_type:
        return_type = Typer(python_type=return_type)
    else:
        cause = Except(
            ERROR,
            "expecting {{function}} to have annotated return type",
            {"function": func_name},
            trace=get_stacktrace(start=3),
        )
        return_type = UnknownTyper(cause)

    if num_args == 0:

        def wrapper0(val, att):
            return func()

        wrapper = wrapper0
    elif num_args == 2 and spec.args[-1].startswith("att"):
        wrapper = func
    else:
        locals = {}
        exec(
            strings.outdent(
                f"""
            def {func_name}(val, att):
                return func(val)            
            """
            ),
            {"func": func},
            locals,
        )
        wrapper = locals[func_name]
        setattr(wrapper, "original", func)

    # copy func name to wrapper for sensible debug output
    wrapper.__name__ = func_name
    return wrapper, return_type


class TopFunctionFactory(FunctionFactory):
    """
    it(x)  RETURNS A FunctionFactory FOR x
    """

    def __call__(self, value):
        if isinstance(value, FunctionFactory):
            logger.error("don't do this")

        if isinstance(value, type):
            # ASSUME THIS IS A CONSTRUCTOR
            typer = CallableTyper(return_type=value)

            def type_builder(domain_type, domain_schema) -> BuiltFunction:
                return BuiltFunction(lambda v, a: value, typer, domain_schema)

            return FunctionFactory(type_builder, typer, f"{value}")

        typer = Typer(python_type=type(value))

        def value_builder(domain_type, domain_schema) -> BuiltFunction:
            return BuiltFunction(lambda v, a: value, typer, domain_schema)

        return FunctionFactory(value_builder, typer, f"{value}")

    def __str__(self):
        return "it"


def noop(v, a):
    return v


def top_builder(domain_type, domain_schema) -> BuiltFunction:
    return BuiltFunction(noop, domain_type, domain_schema)


it = TopFunctionFactory(top_builder, LazyTyper(), "it")
