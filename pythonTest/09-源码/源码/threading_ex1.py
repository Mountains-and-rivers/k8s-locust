__author__ = "Alex Li"

import threading
import time

def run(n):
    print("task ",n )
    time.sleep(2)
    print("task done",n)

start_time = time.time()
t_objs = [] #存线程实例
for i in range(50):
    t = threading.Thread(target=run,args=("t-%s" %i ,))
    t.start()
    t_objs.append(t) #为了不阻塞后面线程的启动，不在这里join，先放到一个列表里

# for t in t_objs: #循环线程实例列表，等待所有线程执行完毕
#     t.join()


print("----------all threads has finished...")
print("cost:",time.time() - start_time)
# run("t1")
# run("t2")