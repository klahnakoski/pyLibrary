from util.logs import Log
from util.struct import Null


def test_none():
    a = 0
    b = 0
    c = None
    d = None

    if a == b:
        pass
    else:
        Log.error("error")

    if c == d:
        pass
    else:
        Log.error("error")

    if a == c:
        Log.error("error")

    if d == b:
        Log.error("error")

    if not c:
        pass
    else:
        Log.error("error")



def test_null():
    a = 0
    b = 0
    c = Null
    d = Null

    if a == b:
        pass
    else:
        Log.error("error")

    if c == d:
        pass
    else:
        Log.error("error")

    if a == c:
        Log.error("error")

    if d == b:
        Log.error("error")

    if c==None:
        pass
    else:
        Log.error("error")


    if not c:
        pass
    else:
        Log.error("error")



def test_list():

    if not []:
        pass
    else:
        Log.error("error")

    if []:
        Log.error("error")


    if not [0]:
        Log.error("error")



test_none()
test_null()
test_list()
