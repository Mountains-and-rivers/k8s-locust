__author__ = "Alex Li"
import json


def sayhi(name):
    print("hello,",name)

info = {
    'name':'alex',
    'age':22,
    #'func':sayhi
}


f = open("test.text","w")
f.write( json.dumps( info) )


info['age'] = 21
f.write( json.dumps( info) )

f.close()