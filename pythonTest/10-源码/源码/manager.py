__author__ = "Alex Li"

from multiprocessing import Process, Manager
import os

def f(d, l):
    d[1] = '1'
    d['2'] = 2
    d["pid%s" %os.getpid()] = os.getpid()
    l.append(1)
    print(l,d)


if __name__ == '__main__':
    with Manager() as manager:
        d = manager.dict()

        l = manager.list(range(5))

        p_list = []
        for i in range(10):
            p = Process(target=f, args=(d, l))
            p.start()
            p_list.append(p)
        for res in p_list:
            res.join()
        l.append("from parent")
        print(d)
        print(l)