from math import log, floor
import gc
from util.env import profiles
from util.env.logs import Log
from util.maths.randoms import Random
from util.struct import Struct, StructList, wrap, slow_wrap
from util.env.profiles import Profiler


def baseline(v):
    return [v]


def test_wrap_1():
    switch = [
        lambda: Struct(i=Random.int(2000)),
        lambda: {"i": Random.int(2000)},
        lambda: StructList([{"i": Random.int(2000)}]),
        lambda: [{"i": Random.int(2000)}]
    ]

    inputs = [switch[min(len(switch) - 1, int(floor(-log(Random.float(), 2))))]() for i in range(1000000)]

    num = 10
    for i in range(num):
        results = []
        gc.collect()
        with Profiler("more struct: slow_wrap"):
            for v in inputs:
                results.append(slow_wrap(v))

        results = []
        gc.collect()
        with Profiler("more struct: wrap"):
            for v in inputs:
                results.append(wrap(v))

        results = []
        gc.collect()
        with Profiler("more struct: baseline"):
            for v in inputs:
                results.append(baseline(v))

        Log.note("Done {{i}} of {{num}}", {"i": i, "num": num})


def test_wrap_2():
    switch = [
        lambda: {"i": Random.int(2000)},
        lambda: Struct(i=Random.int(2000)),
        lambda: StructList([{"i": Random.int(2000)}]),
        lambda: [{"i": Random.int(2000)}]
    ]

    inputs = [switch[min(len(switch) - 1, int(floor(-log(Random.float(), 2))))]() for i in range(1000000)]

    num = 10
    for i in range(num):
        results = []
        gc.collect()
        with Profiler("more dict: slow_wrap"):
            for v in inputs:
                results.append(slow_wrap(v))

        results = []
        gc.collect()
        with Profiler("more dict: wrap"):
            for v in inputs:
                results.append(wrap(v))

        results = []
        gc.collect()
        with Profiler("more dict: baseline"):
            for v in inputs:
                results.append(baseline(v))

        Log.note("Done {{i}} of {{num}}", {"i": i, "num": num})


def test_wrap_3():
    switch = [
        lambda: Random.string(20),
        lambda: {"i": Random.int(2000)},
        lambda: Struct(i=Random.int(2000)),
        lambda: StructList([{"i": Random.int(2000)}]),
        lambda: [{"i": Random.int(2000)}]
    ]

    inputs = [switch[min(len(switch) - 1, int(floor(-log(Random.float(), 2))))]() for i in range(1000000)]

    num = 10
    for i in range(num):
        results = []
        gc.collect()
        with Profiler("more string: slow_wrap"):
            for v in inputs:
                results.append(slow_wrap(v))

        results = []
        gc.collect()
        with Profiler("more string: wrap"):
            for v in inputs:
                results.append(wrap(v))

        results = []
        gc.collect()
        with Profiler("more string: baseline"):
            for v in inputs:
                results.append(baseline(v))

        Log.note("Done {{i}} of {{num}}", {"i": i, "num": num})


profiles.ON = True
Log.start()
test_wrap_1()
test_wrap_2()
test_wrap_3()
profiles.write(Struct(filename="speedtest_wrap.tab"))
Log.stop()
