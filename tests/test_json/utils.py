from mo_dots import listwrap, to_data
from mo_json import value2json


def hex2bytes(value):
    return bytearray.fromhex(value)


def list2tab(rows, separator="\t"):
    columns = set()
    for r in listwrap(rows):
        columns |= set(k for k, v in r.leaves())
    keys = list(columns)

    output = []
    for r in to_data(rows):
        output.append(separator.join(value2json(r[k]) for k in keys))

    return separator.join(keys) + "\n" + "\n".join(output)
