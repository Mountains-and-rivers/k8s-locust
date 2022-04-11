__author__ = "Alex Li"
import sys
#f = open("yesterday2","r",encoding="utf-8")

with open("yesterday2","r",encoding="utf-8") as f ,\
      open("yesterday2", "r", encoding="utf-8") as f2:
    for line in f:
        print(line)

