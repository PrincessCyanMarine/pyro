from Pyro5.api import *
from sys import * 

ns = locate_ns()
print(ns.list())
print(ns.lookup("leader"))

def getLeader():
    return Proxy(ns.lookup("leader"))

act = argv[1]
if act == "add" or act == "set":
    num = int(argv[2])
    newValue = None
    if act == "add":
        newValue = getLeader().add(num)
    else:
        newValue = getLeader().set(num)
    print("New value ", newValue)
elif act == "get":
    print("Value ", getLeader().get())




# uri = input("What is the Pyro uri of the greeting object? ").strip()
# name = input("What is your name? ").strip()

# greeting_maker = Pyro5.api.Proxy(uri)     # get a Pyro proxy to the greeting object
# print(greeting_maker.get_fortune(name))   # call method normally