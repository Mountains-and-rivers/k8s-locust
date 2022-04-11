__author__ = "Alex Li"

def calc(n):
    print(n)
    if int(n/2) >0:
        return calc( int(n/2) )
    print("->",n)


calc(10)