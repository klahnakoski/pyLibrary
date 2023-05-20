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

from mo_json import JxType, JX_TEXT, array_of, JX_IS_NULL
from mo_streams._utils import arg_spec

parse, ANNOTATIONS, ObjectStream = expect("parse", "ANNOTATIONS", "ObjectStream")


class Typer:
    """
    Smooth out the lumps of Python type manipulation
    """


    def __init__(self, *, example=None, python_type=None, function=None):
        if function:
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
        if self.python_type in [int, float]:
            return Typer(python_type=float)
        logger.error("not handled")

    def __call__(self, *args, **kwargs):
        logger.error("programmer error")

    def __str__(self):
        return f"Typer(class={self.python_type.__name__})"


class JxTyper:
    """
    represent Data schema
    """

    def __init__(self, type_):
        self.type_: JxType = type_

    def __getattr__(self, item):
        attribute_type = self.type_[item]
        return Typer(python_type=attribute_type)

        # logger.error(
        #     """expecting {{type}} to have attribute {{item|quote}}""",
        #     type=self.type_,
        #     item=item,
        # )

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
    AN ObjectStream HAS A TYPE TOO
    """

    def __init__(self, member_type, _schema):
        Typer.__init__(self, python_type=ObjectStream)
        if not isinstance(member_type, Typer):
            logger.error("expecting typer")
        self.member_type = member_type
        self._schema = _schema

    def __call__(self, *args, **kwargs):
        logger.error("can not call an ObjectStream")

    @property
    def map(self):
        return MapperTyper(self.member_type, self._schema)

    @property
    def filter(self):
        return CallableTyper(self)

    @property
    def to_list(self):
        return CallableTyper(Typer(python_type=list))

    @property
    def sum(self):
        return CallableTyper(Typer(python_type=float))

    def __getattr__(self, item):
        spec = inspect.getmembers(ObjectStream)
        for k, m in spec:
            if k == item:
                logger.error("add method to handle type inference for ObjectStream")

        output = getattr(self.member_type, item)
        if isinstance(output, UnknownTyper):
            if item in self._schema:
                output = self._schema[item]
                if output:
                    return JxTyper(output)
        return output

    def __str__(self):
        return f"StreamTyper({self.member_type})"


class MapperTyper(Typer):
    """
    REPRESENT THE RETURN TYPE OF THE Stream.map()
    """

    def __init__(self, domain_type, _schema):
        Typer.__init__(self, python_type=ObjectStream)
        self.domain_type = domain_type
        self._schema = _schema

    def __call__(self, return_type):
        return StreamTyper(member_type=return_type, _schema=self._schema)

    def __str__(self):
        return f"MapperTyper({self.member_type}, {self._schema})"


class CallableTyper(Typer):
    """
    ASSUME THIS WILL BE CALLED, AND THIS IS THE TYPE RETURNED
    """

    def __init__(self, return_type):
        if isinstance(return_type, Typer):
            self.type_ = return_type
        else:
            self.type_ = Typer(python_type=return_type)

    def __call__(self, *args, **kwargs):
        return self.type_

    def __getattr__(self, item):
        spec = inspect.getmembers(self.type_)
        for k, m in spec:
            if k == item:
                inspect.ismethod(m)

    def __str__(self):
        return f"CallableTyper(return_type={self.type_})"


class UnknownTyper(Typer):
    """
    MANY TIMES WE DO NOT KNOW THE TYPE, BUT MAYBE WE NEVER NEED IT
    """

    def __init__(self, error):
        Typer.__init__(self)
        self._error: Exception = error

    def __bool__(self):
        return False

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


export("mo_streams.type_parser", Typer)
export("mo_streams.byte_stream", Typer)
