# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from io import BytesIO

from mo_files import File
from mo_imports import expect, export
from mo_logs import logger

from mo_json import JxType, JX_TEXT
from mo_streams._utils import chunk_bytes, Stream

ObjectStream, StringStream, File_usingStream, Typer = expect(
    "ObjectStream", "StringStream", "File_usingStream", "Typer"
)


DEBUG = False


class ByteStream(Stream):
    def __init__(self, reader):
        self.verbose = DEBUG
        self.reader: BytesIO = reader

    def close(self):
        self.reader.close()

    def from_zip(self) -> ObjectStream:
        """
        RETURN A STREAM OF Files
        """
        from zipfile import ZipFile

        def read():
            # ZIP HAS DIRACTORY AT END OF FILE, MUST READ WHOLE THING
            reader = self.reader
            try:
                if not reader.seekable():
                    reader = BytesIO(b"".join(chunk_bytes(reader)))
                with ZipFile(reader, mode="r") as archive:
                    for info in archive.filelist:
                        yield File_usingStream(
                            info.filename, lambda: ByteStream(archive.open(info.filename, "r")),
                        ), {"name": info.filename}
            finally:
                reader.close()

        return ObjectStream(read(), Typer(python_type=File_usingStream), JxType(name=JX_TEXT))

    def from_zst(self):
        """
        :param stream:
        :return:
        """
        from zstandard import ZstdDecompressor

        stream_reader = ZstdDecompressor().stream_reader(self.reader, closefd=True)
        return ByteStream(stream_reader)

    def from_tar(self):
        """
        return a stream of files
        """
        import tarfile

        tf = tarfile.open(mode="r:", fileobj=self.reader)

        def file(info):
            reader = tf.extractfile(info)
            if reader is None:
                # directories
                return File_usingStream(info.name, lambda: None)
            else:
                return File_usingStream(info.name, lambda: ByteStream(tf.extractfile(info)))

        def read():
            try:
                while True:
                    info = tf.next()
                    if not info:
                        return
                    yield file(info), {"name": info.name}
            finally:
                self.reader.close()

        return ObjectStream(read(), Typer(python_type=File_usingStream), JxType(name=JX_TEXT))

    def to_zst(self):
        from zstandard import ZstdCompressor

        return ByteStream(ZstdCompressor().stream_reader(self.reader))

    def utf8(self):
        def read():
            for data in chunk_bytes(self.reader):
                yield data.decode("utf8")
            self.reader.close()

        return StringStream(read())

    def lines(self):
        return self.utf8().lines()

    def chunk(self, size=8192):
        return ObjectStream(chunk_bytes(self.reader, size), b"", bytes, {}, JxType())

    def write(self, file):
        file = File(file)
        with open(file.os_path, "wb") as f:
            for d in chunk_bytes(self.reader):
                f.write(d)

    def to_bytes(self):
        return b"".join(chunk_bytes(self.reader))

    def to_s3(self, *, name, bucket):
        import boto3

        s3_client = boto3.client("s3")
        try:
            return s3_client.upload_fileobj(self.reader, bucket, name)
        except Exception as cause:
            if self.verbose:
                logger.warn("problem with s3 upload", cause=cause)


export("mo_streams._utils", ByteStream)
