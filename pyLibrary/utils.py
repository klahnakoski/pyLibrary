# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from __future__ import division, unicode_literals

import datetime
import re

from jx_python.jx import chunk
from mo_dots import DataObject, Null, from_data
from mo_future import zip_longest
from mo_logs import Log


class Version(object):
    __slots__ = ["prefix", "version"]

    def __new__(cls, version, prefix=""):
        if version == None:
            return Null
        else:
            return object.__new__(cls)

    def __init__(self, version, prefix=""):
        version = from_data(version)

        if isinstance(version, tuple):
            self.version = version
            self.prefix = ("", ".", ".", ".", ".", ".", ".")[:len(self.version)]
        elif not version or isinstance(version, DataObject):
            self.prefix = ('',)
            self.version = (0,)
        elif isinstance(version, Version):
            self.prefix = version.prefix
            self.version = version.version
        else:
            try:
                self.prefix, version = split(version)
            except Exception as cause:
                raise cause

            def scrub(v):
                try:
                    return int(v)
                except Exception:
                    return v

            self.version = tuple(map(scrub, version))
        if len(self.prefix)!=len(self.version):
            Log.error("not expected")

    def __gt__(self, other):
        other = Version(other)
        for s, o in zip_longest(self.version, other.version):
            if s is None and o is not None:
                return False
            if s is not None and o is None:
                return True

            if isinstance(s, str):
                if isinstance(o, str):
                    if s == o:
                        continue
                    return s > o
                else:
                    if int(s) == o:
                        continue
                    return int(s) >= o
            else:
                if isinstance(o, str):
                    if s == int(o):
                        continue
                    return s > int(o)
                else:
                    if s == o:
                        continue
                    return s > o

        return False

    def __ge__(self, other):
        return self == other or self > other

    def __eq__(self, other):
        other = Version(other)
        return self.version == other.version

    def __le__(self, other):
        return self == other or not (self > other)

    def __lt__(self, other):
        return not (self == other) and not (self > other)

    def __ne__(self, other):
        other = Version(other)
        return self.version != other.version

    def __str__(self):
        return "".join(p + str(v) for p, v in zip(self.prefix, self.version))

    def __hash__(self):
        return self.__str__().__hash__()

    def __add__(self, other):
        major, minor, mini = self.version
        minor += other
        mini = datetime.datetime.utcnow().strftime("%y%j")
        return Version((major, minor, mini), prefix=self.prefix)

    __data__ = __str__

    @property
    def major(self):
        return self.version[0]

    @property
    def minor(self):
        return self.version[1]

    @property
    def mini(self):
        return self.version[2]


def triple(version):
    return (tuple(version) + (0, 0, 0))[:3]


def split(version):
    result = re.split(r"(\.|(?<=\d)(?=[a-zA-Z])|(?<=[a-zA-Z])(?=\d)|^(?=\d))", version)
    if len(result) > 2 and not result[1]:
        result.pop(1)
    return zip(*(r for g, r in chunk(result, 2)))


split('v1.10.20029')