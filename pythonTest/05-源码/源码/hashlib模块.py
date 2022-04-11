__author__ = "Alex Li"

#
import hashlib
#
# m = hashlib.md5()
# m.update(b"Hello")
# print(m.hexdigest())
# m.update(b"It's me")
# print(m.hexdigest())
# m.update(b"It's been a long time since we spoken...")
#
m2 = hashlib.md5()
m2.update("HelloIt's me天王盖地虎".encode(encoding="utf-8"))
print(m2.hexdigest())
#
# s2  = hashlib.sha1()
# s2.update(b"HelloIt's me")
# print(s2.hexdigest())


import hmac

h = hmac.new(b"12345","you are 250你是".encode(encoding="utf-8"))
print(h.digest())
print(h.hexdigest())