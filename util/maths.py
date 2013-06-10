#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
from util.debug import D


def bayesian_add(a, b):
    if a>=1 or b>=1 or a<=0 or b<=0: D.error("Only allowed values *between* zero and one")
    return a*b/(a*b+(1-a)*(1-b))

