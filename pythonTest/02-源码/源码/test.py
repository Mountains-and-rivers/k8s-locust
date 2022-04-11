__author__ = "Alex Li"
import copy

person=['name',['saving',100]]
'''
p1=copy.copy(person)
p2=person[:]
p3=list(person)
'''
p1=person[:]
p2=person[:]

p1[0]='alex'
p2[0]='fengjie'

p1[1][1]=50

print(p1)
print(p2)
msg="asda"
print(msg.encode(code='utf-8'))