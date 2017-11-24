import sys


PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2

NoneType = type(None)


if PY3:
    text_type = str
    binary_type = bytes
    long = int
    xrange = range

else:
    import __builtin__

    text_type = __builtin__.unicode
    binary_type = str
    long = __builtin__.long
    xrange = __builtin__.xrange

