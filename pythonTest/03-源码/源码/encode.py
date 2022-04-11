import sys
print(sys.getdefaultencoding())
__author__ = "Alex Li"

s = "你哈"
s_gbk = s.encode("gbk")

print(s_gbk)
print(s.encode())

gbk_to_utf8 = s_gbk.decode("gbk").encode("utf-8")
print("utf8",gbk_to_utf8)