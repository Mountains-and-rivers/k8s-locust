__author__ = "Alex Li"


class Dog:
    def __init__(self,name):
        self.name = name

    def bulk(self):
        print("%s: wang wang wang!" % self.name)


d1 = Dog("陈荣华")
d2 = Dog("陈三炮")
d3 = Dog("陈老泡")

d1.bulk()
d2.bulk()
d3.bulk()
