import sys
import time


def output(sleep=0.2):
    print 'start'
    for i in range(5):
        print 'running iteration %d' % i * 500
        time.sleep(float(sleep))
    print 'done'


globals()[sys.argv[1]](*sys.argv[2:])

