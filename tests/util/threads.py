import sys
from util.debug import D
from util.threads import Lock
from util.multithread import Multithread
import util

def test_lock(num, lock):
    with lock:
        sys.stdout.write("write line "+str(num))



class test_thread(object):


    @staticmethod
    def test_many_threads_on_lock():
        lock=util.threads.Lock()

        with Multithread([test_lock for i in range(10)]) as multi:
            multi.execute([{"lock":lock, "num":i} for i in range(1000)])




Log.start()
test_thread().test_many_threads_on_lock()
Log.stop()