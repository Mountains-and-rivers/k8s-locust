__author__ = "Alex Li"
import copy

#names = "ZhangYang Guyun Xiangpeng XuLiangChen"
'''names = ["4ZhangYang", "#!Guyun","xXiangPeng",["alex","jack"],"ChenRonghua","XuLiangchen"]
print(names[0:-1:2])
print(names[::2])
print(names[:])
#range(1,10,2)

for i in names:
    print(i)

name2 = copy.deepcopy(names)
print(names)
print(name2)
names[2] = "向鹏"
names[3][0] ="ALEXANDER"

print(names)
print(name2)
names.append("LeiHaidong")
names.insert(1,"ChenRonghua")
names.insert(3,"Xinzhiyu")
#names[2] ="XieDi"

#print(names[0],names[2])
#print(names[1:3]) #切片
#print(names[3]) #切片
#print(names[-2:]) #切片
#print(names[0:3]) #切片
#print(names[:3]) #切片

#delete
#names.remove("ChenRonghua")
#del names[1] =names.pop(1)
#names.pop(1)
print(names)
#print(names.index("XieDi"))
#print(   names[names.index("XieDi")]   )

#print(names.count("ChenRonghua"))
#names.clear()
#names.reverse()
#names.sort()
print(names)
names2 = [1,2,3,4]
#names
names.extend(names2)
#del names2
print(names,names2)'''


a  =[1,2,3]
b = a
a[1] =555
b = [1,555,3]