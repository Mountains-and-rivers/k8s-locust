__author__ = "Alex Li"
import pickle

def sayhi(name):
    print("hello2,",name)


f = open("test.text","rb")

data = pickle.loads(f.read())


print(data["func"]("Alex"))

