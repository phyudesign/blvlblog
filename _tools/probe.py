import sys, re; sys.path.insert(0, "_tools")
import monitor as m
h = m.get("https://torecaplaza55.com/")
i = h.find("余福")
print(len(h), i)
print(h[max(0,i-2500):i+600])
