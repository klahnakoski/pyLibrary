# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_imports import export

from mo_json import JxType
from mo_streams._utils import Reader, Stream
from mo_streams.byte_stream import ByteStream
from mo_streams.object_stream import ObjectStream
from mo_streams.type_utils import Typer


class StringStream(Stream):
    def __init__(self, chunks):
        self._chunks = chunks

    def __getattr__(self, item):
        def read():
            for v in self._chunks:
                yield getattr(v, item), {}

        return ObjectStream(read(), getattr(Typer(python_type=str), item), JxType())

    def utf8(self) -> ByteStream:
        return ByteStream(Reader((c.encode("utf8") for c in self._chunks)))

    def lines(self):
        def read():
            line = ""
            end = -1
            try:
                while True:
                    while end == -1:
                        content = next(self._chunks)
                        line += content
                        end = line.find("\n")

                    while end != -1:
                        yield line[:end], {}
                        end += 1
                        line = line[end:]
                        end = line.find("\n")
            except StopIteration:
                if line:
                    yield line, {}

        return ObjectStream(read(), Typer(python_type=str), JxType())

    def to_str(self) -> str:
        return "".join(self._chunks)


export("mo_streams.byte_stream", StringStream)
