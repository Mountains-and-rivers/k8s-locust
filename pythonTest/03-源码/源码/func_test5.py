__author__ = "Alex Li"

def test(x,y,z):
    print(x)
    print(y)
    print(z)

# test(y=2,x=1) #与形参顺序无关
# test(1,2)  #与形参一一对应
#test(x=2,3)
test(3,z=2,y=6)