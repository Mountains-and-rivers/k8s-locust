__author__ = "Alex Li"
import json



f = open("test.text","r")


#data = json.loads(f.read()) #data = pickle.loads(f.read())

for line in f:


    print(json.loads(line))

