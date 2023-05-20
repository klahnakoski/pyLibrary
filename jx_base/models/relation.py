# encoding: utf-8
#
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http:# mozilla.org/MPL/2.0/.
#


from dataclasses import dataclass
from typing import List

from jx_base.models.table import Table


@dataclass
class Relation:
    ones_table: str
    ones_columns: List[str]
    many_table: str
    many_columns: List[str]
