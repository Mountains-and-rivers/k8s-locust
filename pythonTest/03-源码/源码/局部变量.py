__author__ = "Alex Li"

school = "Oldboy edu."
names = ["Alex","Jack","Rain"]
names_tuple = (1,2,3,4)
def change_name():
    names[0] = "金角大王"

    print("inside func",names)

change_name()
print(names)


# def change_name(name):
#     global school
#     school = "Mage Linux"
#     print("before change",name,school)
#     name ="Alex li" #这个函数就是这个变量的作用域
#     age =23
#     print("after change",name)


#
# print("school:",school)
#
# name = "alex"
# change_name(name)
# print(name)

#print("age",age)