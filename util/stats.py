#####
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#####
from math import sqrt


DEBUG=True


def stats2moments(stats):
    free=stats.free

    m = (
        stats.count,
        stats.mean*stats.count,
        (stats.count-free)(stats.std*stats.std) + stats.mean*stats.mean*stats.count
    )
    if DEBUG:
        v = moments2stats(m)
        if v.count!=stats.count or v.std!=stats.std: D.error("convertion error")


def moments2stats(moments, unbiased):
    free=0
    if unbiased: free=1
    N=moments.S[0]
    return Stats(
        count=N,
        mean=moments.S[1]/N,
        std=sqrt((moments.S[2]-(moments.S[1]**2)/N)/(N-free))
    )



class Stats():

    def __init__(self, **args):
        self.count=args["count"]
        self.mean=args["mean"]
        self.std=args["std"]
        self.unbiased=args["unbiased"]






class Moments():
    def __init__(self, *args):
        self.S=tuple(args)

    def __add__(self, other):
        return Moments(self.S[0]+other.S[0], self.S[1]+other.S[1], self.S[2]+other.S[2])

    def __sub__(self, other):
        return Moments(self.S[0]-other.S[0], self.S[1]-other.S[1], self.S[2]-other.S[2])


