

from multiprocessing import Queue
import threading
from util.basic import nvl
from util.debug import D


class etl_worker_thread(threading.Thread):

    #in_queue MUST CONTAIN HASH OF PARAMETERS FOR load()
    def __init__(self, name, in_queue, out_queue, function):
        threading.Thread.__init__(self)
        self.name=name
        self.in_queue=in_queue
        self.out_queue=out_queue
        self.function=function
        self.keep_running=True
        self.start()

    #REQUIRED TO DETECT KEYBOARD, AND OTHER, INTERRUPTS
    def join(self, timeout=None):
        while self.isAlive():
            threading.Thread.join(self, nvl(timeout, 0.5))

    def run(self):
        while self.keep_running:
            params=self.in_queue.get()
            if params=="stop": return
            try:
                result=self.function(**params)
                if self.keep_running:
                    self.out_queue.put(result)
            except Exception, e:
                D.warning("Can not load data for params=${params}", {"params": params})
                if self.keep_running:
                    self.out_queue.put([])







#PASS A SET OF FUNCTIONS TO BE EXECUTED (ONE PER THREAD)
#PASS AN (ITERATOR/LIST) OF PARAMETERS TO BE ISSUED TO NEXT AVAILABLE THREAD
class Multithread():

    def __init__(self, functions):
        self.outbound=Queue()
        self.inbound=Queue()

        #MAKE THREADS
        self.threads=[]
        for t in range(len(functions)):
            thread=etl_worker_thread("worker "+str(t), self.inbound, self.outbound, functions[t])
            self.threads.append(thread)



    def __enter__(self):
        return self

    def __exit__(self, a, b, c):
        try:
            #SEND ENOUGH STOPS
            for t in self.threads:
                self.inbound.put("stop")

            #WAIT FOR FINISH
            for t in self.threads:
                t.join()
        except (KeyboardInterrupt, SystemExit):
            D.println("Shutdow Started, please be patient")
        except Exception, e:
            D.error("Unusual shutdown!", e)
        finally:
            for t in self.threads:
                t.keep_running=False
            for t in self.threads:
                t.join()


    #RETURN A GENERATOR THAT HAS len(parameters) RESULTS (ANY ORDER)
    def execute(self, parameters):
        #FILL QUEUE WITH WORK
        for param in parameters:
            self.inbound.put(param)

        num=len(parameters)
        for i in xrange(num):
            result=self.outbound.get()
            yield result

    def stop(self):
        for t in self.threads:
            t.keep_running=False
        self.threads=[]
        self.inbound.close()
        self.outbound.close()

