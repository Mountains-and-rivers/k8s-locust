__author__ = "Alex Li"


class Role:
    n = 123 #类变量
    n_list = []
    name = "我是类name"
    def __init__(self, name, role, weapon, life_value=100, money=15000):
        #构造函数
        #在实例化时做一些类的初始化的工作
        self.name = name #r1.name=name实例变量(静态属性),作用域就是实例本身
        self.role = role
        self.weapon = weapon
        self.__life_value = life_value
        self.money = money
    def __del__(self):
        pass #print("%s 彻底死了。。。。" %self.name)

    def show_status(self):
        print("name:%s weapon:%s life_val:%s" %(self.name,
                                                 self.weapon,
                                                self.__life_value))
    def __shot(self): # 类的方法，功能 （动态属性）
        print("shooting...")

    def got_shot(self):
        self.__life_value -=50
        print("%s:ah...,I got shot..."% self.name)

    def buy_gun(self, gun_name):
        print("%s just bought %s" % (self.name,gun_name) )



r1 = Role('Chenronghua', 'police',  'AK47') # Role(r1,'Alex', 'police',  'AK47')把一个类变成一个具体对象的过程叫 实例化(初始化一个类，造了一个对象)
r1.buy_gun("AK47")
r1.got_shot()
r1.__shot()
print(r1.show_status())



r2 = Role('jack', 'terrorist', 'B22')  #生成一个角色
r2.got_shot()
# r1.name = "陈荣华"
# r1.n_list.append("from r1")
# r1.bullet_prove = True
# r1.n = "改类变量"
# print("r1:",r1.weapon,r1.n )
# #del r1.weapon
#
#
#
#
# #print(r1.n,r1.name,r1.bullet_prove,r1.weapon)
#
# #
# r2 = Role('jack', 'terrorist', 'B22')  #生成一个角色
# r2.name = "徐良伟"
# r2.n_list.append("from r2")
# print("r2:",r2.name,r2.n,r2.n_list)
# # r2.got_shot() #Role.got_shot(r2)
#
# Role.n = "ABC"
# print(Role.n_list)
#
# print(r1.n ,r2.n )
