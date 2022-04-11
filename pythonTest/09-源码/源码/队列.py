__author__ = "Alex Li"

import queue

q = queue.PriorityQueue()

q.put((-1,"chenronghua"))
q.put((3,"hanyang"))
q.put((10,"alex"))
q.put((6,"wangsen"))

print(q.get())
print(q.get())
print(q.get())
print(q.get())


# q  = queue.LifoQueue()
#
# q.put(1)
# q.put(2)
# q.put(3)
# print(q.get())
# print(q.get())
# print(q.get())

