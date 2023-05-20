# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import inspect

from mo_imports import expect, export
from mo_logs import logger

from jx_python.streams.inspects import arg_spec
from jx_python.streams.type_parser import parse
from mo_json import JxType, JX_TEXT, JX_IS_NULL, array_of as _array_of, JX_ANY

ANNOTATIONS, Stream = expect("ANNOTATIONS", "Stream")


class Typer:
    """
    Smooth out the lumps of Python type manipulation
    """

    def __init__(self, *, example=None, python_type=None, function=None, array_of=None):
        if array_of:
            self.python_type = _array_of(array_of.python_type)
        elif function:
            # find function return type
            inspect.signature(function)
        elif example:
            self.python_type = type(example)
        elif python_type is LazyTyper:
            self.__class__ = LazyTyper
        else:
            self.python_type = python_type

    def __getattr__(self, item):
        try:
            attribute_type = self.python_type.__annotations__[item]
            return Typer(python_type=attribute_type)
        except:
            pass

        desc = arg_spec(self.python_type, item)
        if desc:
            return_type = desc.annotations.get("return")
            if return_type:
                return parse(return_type)
        return_type = ANNOTATIONS.get((self.python_type, item))
        if return_type:
            return return_type

        return UnknownTyper(lambda t: logger.error(
            """expecting {{type}} to have attribute {{item|quote}} declared with a type annotation""",
            type=self.python_type.__name__,
            item=item,
        ))

    def __add__(self, other):
        if self.python_type is str or other.typer is str:
            return Typer(python_type=str)
        logger.error("not handled")

    def __call__(self, *args, **kwargs):
        spec = inspect.getfullargspec(self.python_type)

    def __str__(self):
        return f"Typer(class={self.python_type.__name__})"


class JxTyper:
    """
    represent Data schema
    """

    def __init__(self, type_):
        self.type_: JxType = type_

    def __getattr__(self, item):
        if self.type_ is JX_ANY:
            return self
        attribute_type = self.type_[item]
        if isinstance(attribute_type, JxType):
            return JxTyper(attribute_type)
        return Typer(python_type=attribute_type)

    __getitem__ = __getattr__

    def __add__(self, other):
        if self.type_ != other.typer:
            logger.error("Can not add two different types")
        if self.type_ == JX_TEXT:
            # ADDING STRINGS RESULTS IN AN ARRAY OF STRINGS
            return array_of(JX_TEXT)
        return self

    def __call__(self, *args, **kwargs):
        return JX_IS_NULL

    def __str__(self):
        return f"JxTyper({self.type_})"


class StreamTyper(Typer):
    """
    AN Stream HAS A TYPE TOO
    """

    def __init__(self, python_type, schema_):
        self.type_ = python_type
        self.schema_ = schema_

    def __call__(self, *args, **kwargs):
        logger.error("can not call an Stream")

    def __getattr__(self, item):
        spec = inspect.getmembers(Stream)
        for k, m in spec:
            if k == item:
                inspect.ismethod(m)

        output = getattr(self.type_, item)
        if isinstance(output, UnknownTyper):
            if item in self._schema:
                output = self._schema[item]
                if output:
                    return JxTyper(output)
        return output

    def __str__(self):
        return f"StreamTyper({self.type_})"


class CallableTyper(Typer):
    """
    ASSUME THIS WILL BE CALLED, AND THIS IS THE TYPE RETURNED
    """

    def __init__(self, python_type):
        self.type_ = python_type

    def __call__(self, *args, **kwargs):
        return Typer(python_type=self.type_)

    def __getattr__(self, item):
        spec = inspect.getmembers(self.type_)
        for k, m in spec:
            if k == item:
                inspect.ismethod(m)

    def __str__(self):
        return f"CallableTyper(return_type={self.type_.__name__})"


class UnknownTyper(Typer):
    """
    MANY TIMES WE DO NOT KNOW THE TYPE, BUT MAYBE WE NEVER NEED IT
    """

    def __init__(self, error):
        Typer.__init__(self)
        self._error: Exception = error

    def __getattr__(self, item):
        def build(type_):
            return getattr(type_, item)

        return UnknownTyper(build)

    def __call__(self, *args, **kwargs):
        def build(type_):
            return type_()

        return UnknownTyper(build)

    def __str__(self):
        return "UnknownTyper()"


class LazyTyper(Typer):
    """
    PLACEHOLDER FOR STREAM ELEMENT TYPE, UNKNOWN DURING LAMBDA DEFINITION
    """

    def __init__(self, resolver=None):
        Typer.__init__(self)
        self._resolver = resolver or (lambda t: t)

    def __getattr__(self, item):
        def build(type_):
            return getattr(type_, item)

        return LazyTyper(build)

    def __call__(self, *args, **kwargs):
        def build(type_):
            return type_

        return LazyTyper(build)

    def __str__(self):
        return "LazyTyper()"


export("jx_python.streams.type_parser", CallableTyper)
