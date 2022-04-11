__author__ = "Alex Li"
import random
checkcode=''
for i in range(5):
    current=random.randrange(0,5)
    if current == i:
        tmp=chr(random.randint(65,90))
    else:
        tmp=random.randint(0,9)
    checkcode+=str(tmp)
print(checkcode)