# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
import inspect
from io import RawIOBase, BytesIO
from typing import BinaryIO

from mo_dots.lists import Log
from mo_imports import expect
from mo_logs import logger

ByteStream = expect("ByteStream")
START, CURRENT, END = 0, 1, 2


class Stream:
    pass


class Reader(BinaryIO):
    """
    WRAP A GENERATOR WITH A FILE-LIKE OBJECT
    """

    def __init__(self, chunks):
        self._chunks = chunks
        self.residue = b""
        self.count = 0

    def readable(self):
        return True

    def read(self, size=-1):
        if not self._chunks:
            return self._more(size)

        try:
            if size == -1:
                data = next(self._chunks)
                self.count += len(data)
                return data

            while len(self.residue) < size:
                chunk = next(self._chunks)
                self.residue += chunk
        except StopIteration:
            self._chunks = None
        return self._more(size)

    def _more(self, size):
        data = self.residue[:size]
        self.residue = self.residue[size:]
        self.count += len(data)
        return data

    def tell(self):
        return self.count

    def seek(self, position, whence=START):
        if whence == END:
            everything = BytesIO(b"".join(self._chunks))

        if self.count > position:
            raise NotImplementedError()
        self.read(position - self.count)


class Writer(RawIOBase):
    """
    REPLACE IO SO THAT WE CAN read() THE RESULTING
    """

    def __init__(self):
        self._buffer = b""

    def writable(self):
        return True

    def seekable(self):
        return False

    def write(self, b):
        if self.closed:
            raise Exception("stream was closed")
        self._buffer += b
        return len(b)

    def read(self, size=-1):
        if size == -1 or size > len(self._buffer):
            chunk = self._buffer
            self._buffer = b""
            return chunk

        chunk = self._buffer[:size]
        self._buffer = self._buffer[size:]
        return chunk

    def content(self):
        return ByteStream(self)

    def size(self):
        return len(self._buffer)


def chunk_bytes(reader, size=4096):
    """
    WRAP A FILE-LIKE OBJECT TO LOOK LIKE A GENERATOR
    """

    if isinstance(reader, ByteStream):
        reader = reader.reader
    if isinstance(reader, Reader):
        return reader._chunks

    def read():
        """
        :return:
        """
        try:
            while True:
                data = reader.read(size)
                if not data:
                    return
                yield data
        except Exception as e:
            Log.error("Problem iterating through stream", cause=e)
        finally:
            try:
                reader.close()
            except Exception as cause:
                pass

    return read()


def is_function(value):
    if type(value).__name__ == "function":
        return True
    if isinstance(value, type):
        return True
    if hasattr(value, "__call__"):
        logger.error("not expected")
    return False


def arg_spec(type_, item):
    for name, func in inspect.getmembers(type_):
        if name != item:
            continue
        return inspect.getfullargspec(func)
