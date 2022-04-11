__author__ = "Alex Li"

import os
# os.system()
# os.mkdir()

class Dog(object):
    def __init__(self,name):
        self.name = name

    @staticmethod #实际上跟类没什么关系了
    def eat(self):
        print("%s is eating %s" %(self.name,'dd'))

    def talk(self):
        print("%s is talking"% self.name)
d = Dog("ChenRonghua")
d.eat(d)
d.talk()