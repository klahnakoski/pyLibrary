# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


class Table:
    """
    POINT TO A SPECIFIC TABLE IN A CONTAINER
    """

    def __init__(self, full_name):
        self.name = full_name

    def map(self, mapping):
        return self

    def get_relations(self):
        """
        RETURN ALL RELATIONS TO THIS TABLE
        """
        return []

    def __data__(self):
        return self.name

    def partial_eval(self, lang):
        return self
