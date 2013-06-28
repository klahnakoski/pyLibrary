################################################################################
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this file,
## You can obtain one at http://mozilla.org/MPL/2.0/.
################################################################################
## Author: Kyle Lahnakoski (kyle@lahnakoski.com)
################################################################################

import itertools
from util.debug import D

class Q:
    @staticmethod
    def groupby(data, keys=None, size=None):
    #return list of (keys, values) pairs where
    #group by the set of set of keys
    #values is list of all data that has those keys
        if size is not None: return groupby_size(data, size)
        try:
            def keys2string(x): return "|".join([str(x[k]) for k in keys])
            def get_keys(d): return dict([(k, str(d[k])) for k in keys])

            #MUST BE SORTED, OR groupby WILL NOT WORK
            data=sorted(data, key=keys2string)
            #groupby RETURNS valueIter, WHICH IS NO GOOD FOR PICKING THE FIRST
            #ELEMENT (SO I CAN GET THE MULTI-KEY)
            output=[(get_keys(values[0]), values) for values in [list(valueIter) for key, valueIter in itertools.groupby(data, keys2string)]]

            return output
        except Exception, e:
            D.error("Problem grouping", e)




    @staticmethod
    def select(data, field_name):
    #return list with values from field_name
       return [d[field_name] for d in data]



def groupby_size(data, size):
    return [data[i:i+size] for i in range(0, len(data), size)]
