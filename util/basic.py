

def nvl(a, b):
    #pick the first none-null value
    if a is None:
        return b
    return a