# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from mo_future import Mapping
from mo_dots import is_data, join_field, leaves_to_data, concat_field
from mo_dots.datas import register_data, Data
from mo_logs import logger
from mo_logs.strings import wordify


class Configuration(Mapping):
    def __init__(self, config, path="."):
        if not isinstance(config, Mapping) and not is_data(config):
            logger.error("Expecting data, not {{config}}", config=config)
        self._path = path
        self._lookup = leaves_to_data({
            join_field(wordify(path)): value for path, value in Data(**config).leaves()
        })

    def __iter__(self):
        return (k for k, _ in self._lookup.leaves())

    def __len__(self):
        return len(self._lookup)

    def prepend(self, other):
        """
        RECURSIVE COALESCE OF PROPERTIES, BUT WITH other TAKING HIGH PRIORITY
        """
        self._lookup = Configuration(other)._lookup | self._lookup
        return self

    def append(self, other):
        """
        RECURSIVE COALESCE OF PROPERTIES
        """
        self._lookup |= Configuration(other)._lookup
        return self

    def __iadd__(self, other):
        """
        RECURSIVE ACCUMULATION OF PROPERTIES
        """
        self._lookup += Configuration(other)._lookup
        return self

    def __ior__(self, other):
        """
        RECURSIVE COALESCE OF PROPERTIES
        """
        self._lookup |= Configuration(other)._lookup
        return self

    def __or__(self, other):
        output = Configuration(other, self._path)
        output.lookup = self._lookup | output._lookup
        return output

    def __getattr__(self, item):
        clean_path = join_field(wordify(item))
        value = self._lookup[clean_path]
        if value == None:
            logger.error(
                "Expecting configuration {{path|quote}}",
                path=concat_field(self._path, clean_path),
                stack_depth=1,
            )
        if is_data(value):
            return Configuration(value, concat_field(self._path, clean_path))
        return value

    __getitem__ = __getattr__


register_data(Configuration)
