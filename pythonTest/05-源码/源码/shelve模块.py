__author__ = "Alex Li"

import shelve
import datetime
d = shelve.open('shelve_test')  # 打开一个文件
print(d.get("name"))
print(d.get("info"))
print(d.get("date"))

# info =  {'age':22,"job":'it'}
#
# name = ["alex", "rain", "test"]
# d["name"] = name  # 持久化列表
# d["info"] = info  # 持久dict
# d['date'] = datetime.datetime.now()
# d.close()