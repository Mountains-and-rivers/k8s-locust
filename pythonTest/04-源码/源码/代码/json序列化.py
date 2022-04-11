__author__ = "Alex Li"
#import json

import pickle

def sayhi(name):
    print("hello,",name)

info = {
    'name':'alex',
    'age':22,
    'func':sayhi
}


f = open("test.text","wb")
#print(json.dumps(info))
print( )
f.write( pickle.dumps( info) )

f.close()