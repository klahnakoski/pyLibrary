################################################################################
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this file,
## You can obtain one at http://mozilla.org/MPL/2.0/.
################################################################################
## Author: Kyle Lahnakoski (kyle@lahnakoski.com)
################################################################################



import copy
import functools

class Struct(dict):
#ACCESS dict AND OBJECTS LIKE JAVASCRIPT a.b==a["b"]

    
    def __init__(self, **map):
        dict.__init__(self)
        object.__setattr__(self, "__dict__", map)  #map IS A COPY OF THE PARAMETERS

    def __str__(self):
        return dict.__str__(object.__getattribute__(self, "__dict__"))
    
    def __getitem__(self, key):
        d=object.__getattribute__(self, "__dict__")

        if key.find(".")>=0:
            for n in key.split("."):
                d=d[n]
            return wrap(d)

        if key not in d: return None
        return wrap(d[key])

    def __setitem__(self, key, value):
        return Struct.__setattr__(self, key, value)

    def __getattribute__(self, key):
        #SOME dict FUNCTIONS
        if key in ["keys", "values", "items"]:
            d=object.__getattribute__(self, "__dict__")
            return dict.__getattribute__(d, key)
        if key=="dict":
            return object.__getattribute__(self, "__dict__")
        if key=="copy":
            return functools.partial(object.__getattribute__(Struct, "copy"), self)


        return Struct.__getitem__(self, key)


    def __setattr__(self, key, value):
        try:
            d=object.__getattribute__(self, "__dict__")

            if key.find(".")>=0:
                seq=key.split(".")
                for k in seq[0,-1]: d=d[k]
                d[seq[-1]]=value
            d[key]=value
        except Exception, e:
            if key.find(".")>=0:
                seq=key.split(".")
                for k in seq[0,-1]: d=d[k]
                d[seq[-1]]=value
            d[key]=value
            raise e

    def keys(self):
        d=object.__getattribute__(self, "__dict__")
        return d.keys()

    def copy(self):
        d=object.__getattribute__(self, "__dict__")
        return Struct(**copy.deepcopy(d))




class StructList(list):

    def __init__(self, vals):
        list.__init__(self)
        self.extend(vals)
        #self.list=list

    def __getitem__(self, index):
        v=list.__getitem__(self, index)
        return wrap(v)

    def __iter__(self):
        i=list.__iter__(self)
        while True:
            yield wrap(i.next())




def wrap(v):
    if v is None:
        return None
    if isinstance(v, Struct):
        return v
    if isinstance(v, dict):
        m = Struct()
        object.__setattr__(m, "__dict__", v) #INJECT m.__dict__=v SO THERE IS NO COPY
        return m
    if isinstance(v, list):
        return StructList(v)
    return v
