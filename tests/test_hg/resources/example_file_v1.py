# THIS IS TEST FILE
import time

a = time.time()

if a < 1.5 * 1000 * 1000 * 1000:
    print "the past"
else:
    print "the future"
