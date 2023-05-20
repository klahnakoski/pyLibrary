# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import itertools
from typing import Any, Iterator, Dict, Tuple
from zipfile import ZIP_STORED

from mo_dots import list_to_data
from mo_files import File
from mo_future import zip_longest, first
from mo_imports import expect, export
from mo_logs import logger

from mo_json import JxType, JX_INTEGER
from mo_streams import ByteStream
from mo_streams._utils import (
    Reader,
    Writer,
    chunk_bytes,
    Stream,
)
from mo_streams.files import File_usingStream
from mo_streams.function_factory import normalize
from mo_streams.type_utils import Typer, LazyTyper, StreamTyper

DEBUG = False

_get = object.__getattribute__
stream = expect("stream")

ERROR = {}
WARNING = {}
NONE = {}


class ObjectStream(Stream):
    """
    A STREAM OF OBJECTS
    """

    def __init__(self, values, datatype, schema):
        if not isinstance(datatype, Typer) or isinstance(datatype, LazyTyper):
            logger.error(
                "expecting datatype to be Typer not {{type}}", type=datatype.__class__.__name__,
            )
        self._iter: Iterator[Tuple[Any, Dict[str, Any]]] = values
        self.typer: Typer = datatype
        self._schema: JxType = schema

    def __data__(self):
        return [f"...stream({self.typer})..."]

    def __getattr__(self, item):
        type_ = getattr(self.typer, item)

        def read():
            for v, a in self._iter:
                try:
                    yield getattr(v, item), a
                except (StopIteration, GeneratorExit):
                    raise
                except Exception as cause:
                    DEBUG and logger.warn("can not get attribute {{item|quote}}", cause=cause)
                    yield None, a

        return ObjectStream(read(), type_, self._schema)

    def __call__(self, *args, **kwargs):
        type_ = self.typer(*args, **kwargs)

        if type_.python_type == bytes:

            def read_bytes():
                for m, a in self._iter:
                    try:
                        yield m(*args, **kwargs)
                    except (StopIteration, GeneratorExit):
                        raise
                    except Exception:
                        yield None

            return ByteStream(Reader(read_bytes()))

        def read():
            for m, a in self._iter:
                try:
                    yield m(*args, **kwargs), a
                except (StopIteration, GeneratorExit):
                    raise
                except Exception:
                    yield None, a

        return ObjectStream(read(), type_, self._schema)

    def map(self, accessor):
        if isinstance(accessor, str):
            type_ = getattr(self.typer, accessor)
            return ObjectStream(((getattr(v, accessor), a) for v, a in self._iter), type_, self._schema)
        fact = normalize(accessor, self.typer)
        acc_func, acc_type, acc_schema = fact.build(self.typer, self._schema)

        def read():
            for value, attach in self._iter:
                result = None
                try:
                    result = acc_func(value, attach)
                    DEBUG and logger.info(
                        "call {{func}} on {{value}} returns {{result}}", func=acc_func, result=result, value=value
                    )
                    yield result, attach
                except (StopIteration, GeneratorExit):
                    raise
                except Exception as cause:
                    DEBUG and logger.warning("problem operating on {{value}}", value=value, cause=cause)
                    yield result, attach

        return ObjectStream(read(), acc_type, self._schema)

    def filter(self, predicate):
        fact = normalize(predicate)
        f, t, s = fact.build(self.typer, self._schema)

        def read():
            for v, a in self._iter:
                try:
                    if f(v, a):
                        yield v, a
                except (StopIteration, GeneratorExit):
                    raise
                except Exception as cause:
                    pass

        return ObjectStream(read(), self.typer, self._schema)

    def attach(self, **kwargs):
        facts = {k: normalize(v) for k, v in kwargs.items()}
        mapper = {k: f.build(self.typer, self._schema) for k, f in facts.items()}
        more_schema = JxType(**{k: f.return_type for k, f in mapper.items()})

        def read():
            for v, a in self._iter:
                yield v, {**a, **{k: m.function(v, a) for k, m in mapper.items()}}

        return ObjectStream(read(), self.typer, self._schema | more_schema)

    def exists(self):
        def read():
            for v, a in self._iter:
                if v != None:
                    yield v, a

        return ObjectStream(read(), self.typer, self._schema)

    def enumerate(self):
        def read():
            for i, (v, a) in enumerate(self._iter):
                yield v, {**a, "index": i}

        return ObjectStream(read(), self.typer, self._schema | JxType(index=JX_INTEGER))

    def flatten(self):
        def read():
            for v, a in self._iter:
                for vv, aa in stream(v)._iter:
                    yield vv, {**a, **aa}

        return ObjectStream(read(), self.typer, self._schema)

    def reverse(self):
        def read():
            yield from reversed(list(self._iter))

        return ObjectStream(read(), self.typer, schema=self._schema)

    def sort(self, *, key=None, reverse=0):
        if key:
            key = lambda t: key(t[0])

        def read():
            yield from sorted(self._iter, key=key, reverse=reverse)

        return ObjectStream(read(), self.typer, self._schema)

    def distinct(self):
        def read():
            acc = set()
            for v, a in self._iter:
                if v in acc:
                    continue
                acc.add(v)
                yield v, a

        return ObjectStream(read(), self.typer, self._schema)

    def append(self, value):
        def read():
            yield from self._iter
            yield value, {}

        return ObjectStream(read(), self.typer, self._schema)

    def extend(self, values):
        suffix = stream(values)

        def read():
            yield from self._iter
            yield from suffix._iter

        return ObjectStream(read(), self.typer, self._schema | suffix._schema)

    def zip(self, *others):
        streams = [stream(o) for o in others]

        def read():
            yield from zip_longest(self._iter, *(s._iter for s in streams))

        return TupleStream(read(), self._example, self.typer, sum((s._schema for s in streams), JxType()),)

    def limit(self, count):
        def read():
            try:
                for i in range(count):
                    yield next(self._iter)
            except StopIteration:
                pass

        return ObjectStream(read(), self.typer, self._schema)

    def group(self, groupor):
        """
        GROUP BY groupor EXPRESSION, RETURN A stream OF streams
        EACH GROUP HAS ATTACHED group PROPERTY WITH THE EXPRESSION VALUE
        :param groupor:
        :return:
        """
        if isinstance(groupor, str):
            raw_group_function = lambda v: getattr(v, groupor)
        else:
            raw_group_function = groupor

        group_factory = normalize(raw_group_function, return_type=self.typer)
        func = group_factory.build(self.typer, self._schema).function
        group_function = lambda pair: func(*pair)
        group_schema = JxType()  # NOT A REAL TYPE, WE ADD PYTHON TYPES ON THE LEAVES
        setattr(group_schema, "group", group_factory.typer)
        sub_schema = self._schema | group_schema

        def read():
            for group, rows in itertools.groupby(sorted(self._iter, key=group_function), group_function):

                def read_rows():
                    for v, a in rows:
                        yield v, {**a, "group": group}

                # THIS IS A BAD IDEA, ObjectStream CAN GET EXPENSIVE IN A LOOP
                yield ObjectStream(read_rows(), self.typer, sub_schema), {"group": group}

        return ObjectStream(read(), StreamTyper(self.typer, sub_schema), group_schema)

    ###########################################################################
    # TERMINATORS
    ###########################################################################

    def materialize(self):
        return ObjectStream(list(self._iter), self.typer, self._schema)

    def to_list(self):
        return list(v for v, _ in self._iter)

    def to_data(self):
        return list_to_data(list(v for v, _ in self._iter))

    def count(self):
        return sum(1 for _ in self._iter)

    def sum(self):
        return sum(v for v, _ in self._iter)

    def first(self):
        for v, _ in self._iter:
            return v

    def last(self):
        output = None
        for v, _ in self._iter:
            output = v
        return output

    def to_dict(self, key=None):
        """
        CONVERT STREAM TO dict
        :param key: CHOOSE WHICH ANNOTATION IS THE KEY
        """
        if key is None:
            candidates = self._schema.__dict__.keys()
            if len(candidates) != 1:
                logger.error(
                    "expecting attachment to have just one property, not {{num}}", num=len(candidates),
                )
            key = first(candidates)

        return {a[key]: v for v, a in self._iter}

    def to_zip(
        self, compression=ZIP_STORED, allowZip64=True, compresslevel=None,
    ):
        from zipfile import ZipFile, ZipInfo

        type_ = self.typer.python_type
        if type_ is File:
            pass
        elif type_ is File_usingStream:
            pass
        else:
            raise NotImplementedError("expecting stream of Files")

        def read():
            mode = "w"
            writer = Writer()
            with ZipFile(
                writer, mode=mode, compression=compression, allowZip64=allowZip64, compresslevel=compresslevel,
            ) as archive:
                for file, _ in self._iter:
                    info = ZipInfo(file.rel_path)
                    with archive.open(info, mode=mode) as target:
                        for chunk in chunk_bytes(file.bytes()):
                            target.write(chunk)
                            yield writer.read()

            yield writer.read()
            writer.close()

        return ByteStream(Reader(read()))


export("mo_streams.byte_stream", ObjectStream)
export("mo_streams.type_utils", ObjectStream)
