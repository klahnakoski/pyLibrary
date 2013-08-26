import thread
import threading



#SIMPLE LOCK (ACTUALLY, A PYTHON threadind.Condition() WITH notify() BEFORE EVERY RELEASE)
class Lock():
    def __init__(self):
        self.monitor=threading.Condition()

    def __enter__(self):
        self.monitor.acquire()
        return self

    def __exit__(self, a, b, c):
        self.monitor.notify()
        self.monitor.release()

    def wait(self):
        self.monitor.wait()


# SIMPLE MESSAGE QUEUE, multiprocessing.Queue REQUIRES SERIALIZATION, WHICH IS HARD TO USE JUST BETWEEN THREADS
class Queue():
    def __init__(self):
        self.keep_running=True
        self.lock=Lock()
        self.queue=[]

    def __iter__(self):
        while self.keep_running:
            try:
                yield self.pop()
            except StopIteration:
                pass
            except Exception, e:
                D.warning("Tell me about what happends here", e)
                return

    def add(self, value):
        with self.lock:
            if self.keep_running:
                self.queue.append(value)

    def pop(self):
        with self.lock:
            while self.keep_running:
                if len(self.queue)>0:
                    value=self.queue.pop(0)
                    if value==Thread.STOP:  #SENDING A STOP INTO THE QUEUE IS ALSO AN OPTION
                        self.keep_running=False
                        raise StopIteration()
                    return value
                self.lock.wait()
            raise StopIteration()

    def close(self):
        with self.lock:
            self.keep_running=False



class Thread():
    @staticmethod
    def run(func):
        thread.start_new_thread(func, ())


Thread.STOP="stop"









        
