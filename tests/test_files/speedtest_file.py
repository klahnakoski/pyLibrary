import codecs
import io
from mo_logs import Log
from mo_times.timer import Timer


def test_simple(filename):
    with Timer("simple time"):
        with codecs.open(filename, "r", encoding="utf-8") as f:
            for line in f:
                id = int(line.split("\t")[0])
                if id % 10000 == 0:
                    Log.note(str(id))


def test_buffered(filename):
    with Timer("buffered time"):
        with codecs.open(filename, "r", encoding="utf-8", buffering=2 ** 25) as f:
            for line in f:
                id = int(line.split("\t")[0])
                if id % 10000 == 0:
                    Log.note(str(id))


def test_io(filename):
    with Timer("io time"):
        with io.open(filename, "r", buffering=2 ** 25) as f:
            for line in f:
                line = line.decode("utf-8")
                id = int(line.split("\t")[0])
                if id % 10000 == 0:
                    Log.note(str(id))


def test_binary(filename, buffering=2 ** 14):
    with Timer("binary time (buffering=={{buffering}})", {"buffering": buffering}):
        remainder = ""
        with io.open(filename, "rb") as f:
            while True:
                block = f.read(buffering)
                if block == "":
                    if remainder == "":
                        return None
                    return remainder
                lines = (remainder + block).split("\n")
                for line in lines[:-1]:
                    line = line.decode("utf-8")
                    id = int(line.split("\t")[0])
                    if id % 10000 == 0:
                        Log.note(str(id))
                remainder = lines[-1]


def test_simple_binary(filename):
    with Timer("simple binary time"):
        with io.open(filename, "rb") as f:
            for line in f:
                line = line.decode("utf-8")
                id = int(line.split("\t")[0])
                if id % 10000 == 0:
                    Log.note(str(id))

filename = "C:/Users/klahnakoski/git/Datazilla2ElasticSearch/results/recent_old.tab"
test_simple_binary(filename)
test_binary(filename, 2 ** 14)
test_binary(filename, 2 ** 25)
test_io(filename)
test_simple(filename)
test_buffered(filename)
