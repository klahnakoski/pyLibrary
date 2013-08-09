import thread
from multiprocessing import Queue as _Queue
from util.debug import D

class Queue():
    def __init__(self):
        self.keep_running=True
        self.queue=_Queue()

    def __iter__(self):
        while self.keep_running:
            try:
                yield self.pop()
            except Exception, e:
                D.warning("Tell me about what appends here", e)
                return

    def add(self, value):
        self.queue.put(value)

    def pop(self):
        self.queue.get()

    def close(self):
        self.keep_running=False
        self.queue.close()





class Thread():
    @staticmethod
    def run(func):
        thread.start_new_thread(func, ())