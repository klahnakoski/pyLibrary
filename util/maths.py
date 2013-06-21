################################################################################
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this file,
## You can obtain one at http://mozilla.org/MPL/2.0/.
################################################################################
## Author: Kyle Lahnakoski (kyle@lahnakoski.com)
################################################################################
from math import log10, floor
import math

from util.debug import D


def bayesian_add(a, b):
    if a>=1 or b>=1 or a<=0 or b<=0: D.error("Only allowed values *between* zero and one")
    return a*b/(a*b+(1-a)*(1-b))



# FOR GOODNESS SAKE - IF YOU PROVIDE A METHOD abs(), PLEASE PROVIDE IT'S COMPLEMENT
# x = abs(x)*sign(x)
# FOUND IN numpy, BUT WE USUALLY DO NOT NEED TO BRING IN A BIG LIB FOR A SIMPLE DECISION
def sign(v):
    if v<0: return -1
    if v>0: return +1
    return 0



def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def round_sci(value, decimal=None, digits=None):

    if digits is not None:
        m=pow(10, floor(log10(digits)))
        return round(value/m, digits)*m

    return round(value, decimal)
