from itertools import groupby

class Q:
    @classmethod
    def groupby(cls, data, keys):
    #return list of (keys, values) pairs where
    #group by the set of set of keys
    #values is list of all data that has those keys
        def keys2string(x): return "|".join([str(x[k]) for k in keys])
        def get_keys(d): return dict([(k, str(d[k])) for k in keys])

        output=[(get_keys(values[0]), values) for key, values in groupby(data, keyfunc=keys2string)]

        return output


    @classmethod
    def select(cls, data, field_name):
    #return list with values from field_name
       return [d[field_name] for d in data]


