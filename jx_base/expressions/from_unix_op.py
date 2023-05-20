# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from jx_base.expressions.expression import Expression
from mo_json.types import JX_NUMBER


class FromUnixOp(Expression):
    """
    FOR USING ON DATABASES WHICH HAVE A DATE COLUMNS: CONVERT TO UNIX
    """

    _data_type = JX_NUMBER

    def __init__(self, *term):
        Expression.__init__(self, *term)
        self.value = term

    def vars(self):
        return self.value.vars()

    def map(self, map_):
        return FromUnixOp(self.value.map(map_))

    def missing(self, lang):
        return self.value.missing(lang)
