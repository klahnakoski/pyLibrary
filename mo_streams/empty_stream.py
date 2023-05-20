# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from mo_dots import Null

from mo_json import JX_IS_NULL
from mo_streams.type_utils import Typer

from mo_streams.object_stream import ObjectStream
from mo_streams._utils import Stream


class EmptyStream(Stream):
    def to_dict(self):
        return {}

    def to_list(self):
        return []

    def to_bytes(self):
        return b""

    def to_str(self):
        return ""

    def first(self):
        return None

    def append(self, value):
        def read():
            yield value, {}

        return ObjectStream(read(), Typer(example=value), JX_IS_NULL)

    def to_data(self):
        return Null

    def sum(self):
        return None

    def last(self):
        return None


def return_self(self, *args, **kwargs):
    return self


for prop in vars(ObjectStream):
    if hasattr(EmptyStream, prop):
        continue
    setattr(EmptyStream, prop, return_self)
