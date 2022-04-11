__author__ = "Alex Li"

import shutil

# f1 = open("本节笔记",encoding="utf-8")
#
# f2 = open("笔记2","w",encoding="utf-8")
# shutil.copyfileobj(f1,f2)

#shutil.copyfile("笔记2","笔记3")
#shutil.copystat("本节笔记","笔记3")

#shutil.copytree("test4","new_test4")
#shutil.rmtree("new_test4")

#shutil.make_archive("shutil_archive_test", "zip","E:\PycharmProjects\pyday1\day5")



import zipfile

z = zipfile.ZipFile("day5.zip","w")

z.write("p_test.py")
print("-----")
z.write("笔记2")

z.close()
