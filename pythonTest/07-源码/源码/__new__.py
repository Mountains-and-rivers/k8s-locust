__author__ = "Alex Li"


# class Foo(object):
#     def __init__(self, name):
#         self.name = name
#
#
# f = Foo("alex")
# print(type(f))
# print(type(Foo))


def func(self):
    print('hello %s' %self.name)
def __init__(self,name,age):
    self.name = name
    self.age = age

Foo = type('Foo', (object,), {'talk': func,
                       '__init__':__init__})
f = Foo("Chrn",22)
f.talk()
print(type(Foo))