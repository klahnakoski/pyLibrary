# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_files import File
from mo_imports import export

from mo_future import extend
from mo_streams._utils import ByteStream

DECODERS = {
    "zst": ByteStream.from_zst,
    "tar": ByteStream.from_tar,
    "zip": ByteStream.from_zip,
    # "gzip": gzip_stream
}


def _get_file_stream(file, stream):
    """
    RETURN A STREAM FROM THE GIVEN FILE
    :param file:
    :return:
    """
    name, extension = _get_extension(file)
    decoder = DECODERS.get(extension, None)
    if not decoder:
        return stream
    return _get_file_stream(name, decoder(stream))


@extend(File)
def content(self):
    return _get_file_stream(self.os_path, ByteStream(open(self.os_path, "rb")))


@extend(File)
def bytes(self):
    return ByteStream(open(self.os_path, "rb"))


def _get_extension(file_name):
    parts = file_name.split(".")
    if len(parts) > 1:
        name = ".".join(parts[:-1])
        extension = parts[-1]
        return name, extension
    return file_name, ""


class File_usingStream:
    """
    A File USING A BORROW STREAM.  FOR USE IN TAR AND ZIP FILES
    """

    rel_path: str

    def __init__(self, rel_path, content):
        self.rel_path = rel_path
        self._content = content

    def content(self):
        return self._content()

    def bytes(self):
        return self._content()


export("mo_streams.byte_stream", File_usingStream)
