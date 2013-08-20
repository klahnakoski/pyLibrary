################################################################################
## This Source Code Form is subject to the terms of the Mozilla Public
## License, v. 2.0. If a copy of the MPL was not distributed with this file,
## You can obtain one at http://mozilla.org/MPL/2.0/.
################################################################################
## Author: Kyle Lahnakoski (kyle@lahnakoski.com)
################################################################################

import threading
from util.basic import nvl
from util.debug import D
from util.threads import Queue



STOP="stop"


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
            params=self.in_queue.pop()
            if params==STOP: return
            try:
                result=self.function(**params)
                if self.keep_running:
                    self.out_queue.add(result)
            except Exception, e:
                D.warning("Can not load data for params=${params}", {"params": params})
                if self.keep_running:
                    self.out_queue.add([])







#PASS A SET OF FUNCTIONS TO BE EXECUTED (ONE PER THREAD)
#PASS AN (ITERATOR/LIST) OF PARAMETERS TO BE ISSUED TO NEXT AVAILABLE THREAD
class Multithread():


    def __init__(self, functions):
        self.outbound=Queue()
        self.inbound=Queue()

        #MAKE THREADS
        self.threads=[]
        for t, f in enumerate(functions):
            thread=etl_worker_thread("worker "+str(t), self.inbound, self.outbound, f)
            self.threads.append(thread)



    def __enter__(self):
        return self

    def __exit__(self, a, b, c):
        try:
            #SEND ENOUGH STOPS
            for t in self.threads:
                self.inbound.add(STOP)

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
            self.inbound.add(param)

        num=len(parameters)
        def output():
            for i in xrange(num):
                result=self.outbound.pop()
                yield result
        return output()

    def stop(self):
        for t in self.threads:
            t.keep_running=False
        self.threads=[]
        self.inbound.close()
        self.outbound.close()


