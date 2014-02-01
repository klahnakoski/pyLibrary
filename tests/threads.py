import sys
import unittest
from util.env.logs import Log
from util.thread.multithread import Multithread
import util


def using_lock(num, lock):
    with lock:
        sys.stdout.write("write line " + str(num))


class TestThread(unittest.TestCase):
    def setUp(self):
        Log.start()

    def tearDown(self):
        Log.stop()

    def test_many_threads_on_lock(self):
        lock = util.threads.Lock()

        with Multithread([using_lock for i in range(10)]) as multi:
            multi.execute([{"lock": lock, "num": i} for i in range(1000)])




