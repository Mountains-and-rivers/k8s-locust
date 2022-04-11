__author__ = "Alex Li"
#key-value
'''
av_catalog = {
    "欧美":{
        "www.youporn.com": ["很多免费的,世界最大的","质量一般"],
        "www.pornhub.com": ["很多免费的,也很大","质量比yourporn高点"],
        "letmedothistoyou.com": ["多是自拍,高质量图片很多","资源不多,更新慢"],
        "x-art.com":["质量很高,真的很高","全部收费,屌比请绕过"]
    },
    "日韩":{
        "tokyo-hot":["质量怎样不清楚,个人已经不喜欢日韩范了","听说是收费的"]
    },
    "大陆":{
        "1024":["全部免费,真好,好人一生平安","服务器在国外,慢"]
    }
}

av_catalog["大陆"]["1024"][1] = "可以在国内做镜像"

av_catalog.setdefault("大陆",{"www.baidu.com":[1,2]})
print(av_catalog)


info = {
    'stu1101': "TengLan Wu",
    'stu1102': "LongZe Luola",
    'stu1103': "XiaoZe Maliya",
}

b ={
    'stu1101': "Alex",
    1:3,
    2:5
}

info.update(b)
print(info )
c = dict.fromkeys([6,7,8],[1,{"name":"alex"},444])
print(c )
c[7][1]['name'] = "Jack Chen"
print(c)'''
#print(info.items() )

#info['stu1104']
#print(info.get('stu1103'))

#print('stu1103' in info) #info.has_key("1103") in py2.x




'''
#print(info["stu1101"])
info["stu1101"] ="武藤兰"
info["stu1104"] ="CangJingkong"

#del
#del info["stu1101"]
info.pop("stu1101")
info.popitem()
print(info)
print("stu1104" in info)
'''

#字典没下标
info = {
    'stu1101': "TengLan Wu",
    'stu1102': "LongZe Luola",
    'stu1103': "XiaoZe Maliya",
}

for i in info:
    print(i,info[i])

for k,v in info.items():
    print(k,v)