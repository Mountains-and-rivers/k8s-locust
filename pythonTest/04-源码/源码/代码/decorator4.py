__author__ = "Alex Li"
import time
def timer(func): #timer(test1)  func=test1
    def deco(*args,**kwargs):
        start_time=time.time()
        func(*args,**kwargs)   #run test1()
        stop_time = time.time()
        print("the func run time  is %s" %(stop_time-start_time))
    return deco
@timer  #test1=timer(test1)
def test1():
    time.sleep(1)
    print('in the test1')

@timer # test2 = timer(test2)  = deco  test2(name) =deco(name)
def test2(name,age):
    print("test2:",name,age)

test1()
test2("alex",22)