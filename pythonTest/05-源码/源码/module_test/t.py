__author__ = "Alex Li"
import time

x=time.localtime(123213123)
print(x)
# print(help(x))
print(x.tm_year)
print('this is 1973 day:%d' %x.tm_yday)