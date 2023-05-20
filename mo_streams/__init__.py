# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import Data
from mo_dots.lists import is_many, is_finite
from mo_files import File
from mo_imports import export

from mo_future import first
from mo_json import JxType, JX_TEXT
from mo_streams._utils import Stream, Reader
from mo_streams.byte_stream import ByteStream
from mo_streams.empty_stream import EmptyStream
from mo_streams.files import content, File_usingStream
from mo_streams.function_factory import it
from mo_streams.object_stream import ObjectStream, ERROR, WARNING, NONE
from mo_streams.string_stream import StringStream
from mo_streams.type_utils import Typer, CallableTyper, StreamTyper, LazyTyper


def stream(value):
    if isinstance(value, (dict, Data)):
        kv = first(value.items())
        if not kv:
            return EmptyStream()
        _, example = kv
        return ObjectStream(((v, {"key": k}) for k, v in value.items()), Typer(example=example), JxType(key=JX_TEXT),)
    elif isinstance(value, bytes):
        return ByteStream(Reader(iter([value])))
    elif isinstance(value, str):
        return StringStream(iter([value]))
    elif value == None:
        return EmptyStream
    elif isinstance(value, Stream):
        return value
    elif isinstance(value, type(range(1))):
        return ObjectStream(((v, {}) for v in value), Typer(example=value.stop), JxType())
    elif is_finite(value):
        example = first(value)

        def read_from_list():
            for v in value:
                yield v, {}

        return ObjectStream(read_from_list(), Typer(example=example), JxType())
    elif is_many(value):
        example = first(value)

        def read():
            yield example, {}
            for v in value:
                yield v, {}

        return ObjectStream(read(), Typer(example=example), JxType())
    else:
        return ObjectStream(iter([(value, {})]), Typer(example=value), JxType())


ANNOTATIONS = {
    (str, "encode"): CallableTyper(return_type=bytes),
    (File_usingStream, "content"): CallableTyper(return_type=ByteStream),
    (File, "content"): CallableTyper(return_type=ByteStream),
    (ByteStream, "utf8"): CallableTyper(return_type=StringStream),
    (StringStream, "lines"): CallableTyper(return_type=StreamTyper(
        member_type=Typer(python_type=str), _schema=JxType()
    )),
    (ByteStream, "lines"): CallableTyper(return_type=StreamTyper(
        member_type=Typer(python_type=str), _schema=JxType()
    )),
    (ObjectStream, "map"): CallableTyper(return_type=StreamTyper(member_type=LazyTyper(), _schema=JxType())),
}

export("mo_streams.object_stream", stream)
export("mo_streams.type_utils", ANNOTATIONS)
