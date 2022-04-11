__author__ = "Alex Li"

import hashlib

m = hashlib.md5()
m.update(b"test")
m.update(b"abc")
print(m.hexdigest())
m2 = hashlib.md5()
m2.update(b"testabc")
print(m2.hexdigest())