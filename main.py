LEADER_TIMEOUT = 1000
MIN_TIMEOUT = 1000
MAX_TIMEOUT = 5000
AUTO_LEADER = None # "p1"

from sys import *
from Pyro5.api import *
from random import *
from time import *
from threading import *
import math
# from javascript import require, globalThis
seed(None)


class MyTimer:
    def _randomInterval(self):
        return randint(MIN_TIMEOUT, MAX_TIMEOUT)
    def __init__(self, callback, autoStart = True, autoReset = True, interval = None):
        self.callback = callback
        self.interval = interval if interval else self._randomInterval() / 1000
        self.autoReset = autoReset
        # print("starting timer with interval ", self.interval, "s")
        if autoStart:
            self.start()
    def _callback(self):
        # print("ATIVO" if self.active else "INATIVO")
        if self.active:
            # print("RUNNING")
            self.callback()
        if self.autoReset:
            self.cancel()
            self.start()
    def start(self):
        # print("Timer starting", self.interval)
        self.timer = Timer(self.interval, self._callback)
        self.timer.start()
        self.active = True
        # self.timer = globalThis.setTimeout(self._callback, self.interval)
    def cancel(self):
        # print("timer cancelado")
        if self.timer:
            self.timer.cancel()
        self.timer = None
        self.active = False
        # print(self.timer, self.active)

commited = 0
uncommited = 0

# def commit():
#     print("Commiting ", commited)
#     nodes = getNodes()
#     for id in nodes:
#         if id != selfId:
#             try:
#                 nodes[id].commit(commited)
#             except:
#                 print("Error ", id, " didn't answer")

def getConsensus(options):
    _options = {}
    for n in options:
        if n not in _options:
            _options[n] = 1
        else:
            _options[n] += 1
    maxNum = 0
    max = None
    for n in _options:
        if _options[n] > maxNum:
            maxNum = _options[n]
            max = n
        elif _options[n] == maxNum:
            max = None
    if maxNum > math.ceil(len(options) / 2):
        return max
    return None

def getConsensusAndCommit(options):
    global commited
    consensus = getConsensus(options)
    print("Consensus ", consensus)
    if consensus:
        commited = consensus
    return commited


@expose
class GreetingMaker(object):
    global leader, term, timer
    def addCandidate(self, term, candidate):
        print("Add candidate ", term, candidate)
        return addCandidate(term, candidate)
    def receiveHeartbeat(self, _leader, _term, _newValue):
        global leader, term, timer, commited
        print("receiveHeartbeat")
        if _term < term:
            return
        timer.cancel()
        newTerm = _term > term
        if newTerm: timer = None
        leader = _leader
        term = _term
        if _newValue != commited:
            commited = _newValue
            print("Commited ", commited)
        # if newTerm: timer = MyTimer(runTimer, False, True)
        # timer.start()
    def test(self, num):
        print("TEST", num, __name__)
    def add(self, num):
        if leader == selfId:
            uncommited = num + commited
            nums = [uncommited]
            print("Adding ", num)
            for node in getNodes():
                if node != selfId:
                    try:
                        nums.append(getNodes()[node].add(num))
                    except:
                        print("Error ", node, " didn't answer")
            return getConsensusAndCommit(nums)
        else:
            print(commited, "+", num, "=", commited + num)
            uncommited = commited + num
            return commited + num
    def set(self, num):
        if leader == selfId:
            uncommited = num
            nums = [uncommited]
            print("Setting ", num)
            for node in getNodes():
                if node != selfId:
                    try:
                        nums.append(getNodes()[node].set(num))
                    except:
                        print("Error ", node, " didn't answer")
            return getConsensusAndCommit(nums)
        else:
            print("New value =", num)
            uncommited = num
            return num
    def get(self):
        if leader == selfId:
            nums = [commited]
            print("Getting")
            for node in getNodes():
                if node != selfId:
                    try:
                        nums.append(getNodes()[node].get())
                    except:
                        print("Error ", node, " didn't answer")
            return getConsensusAndCommit(nums)
        else:
            print("Getting", commited)
            return commited
    def commit(self, num):
        global commited
        commited = num
        print("Commited ", commited)

            

num = int(argv[1])
server = Daemon(port=8080 + num)
selfId = "p" + str(num)
selfNode = server.register(GreetingMaker, selfId)
print("Ready. ", selfNode)
def getNodes():
    return {
        "p1": Proxy("PYRO:p1@localhost:8081"),
        "p2": Proxy("PYRO:p2@localhost:8082"),
        "p3": Proxy("PYRO:p3@localhost:8083"),
        "p4": Proxy("PYRO:p4@localhost:8084"),
    }
candidates = []
term = 0
vote = None
leader = None

def startElection():
    global term, candidates, leader, vote, timer
    votes = []
    def countVotes():
        # print("Votes ", votes)
        if len(votes) == 0:
            return None
        else:
            winner = getConsensus(votes)
            if winner:
                print("Election finished. Winner is ", winner)
            else:
                print("Election finished. No winner")
            return winner
    print("STARTING ELECTION")
    candidates = []
    term = term + 1
    votes.append(selfId)
    candidates.append(selfId)
    nodes = getNodes()
    vote = selfId
    for id in nodes:
        if id != selfId:
            node = nodes[id]
            # print("THREAD", __name__)
            print("Request vote ", id, term, candidates, node)
            try:
                _vote = node.addCandidate(term, candidates)
                # print("Vote ", id, _vote)
                votes.append(_vote)
            except Exception as e:
                print("Error ", id, " didn't answer")
                print(e)
    _leader = countVotes()
    if _leader:
        print("Leader is ", _leader)
        if (_leader == selfId):
            sendHeartbeat()
            leader = _leader
            print("I'm the leader")
            ns = locate_ns()
            ns.register("leader", selfNode)
            timer.cancel()
            timer = MyTimer(runTimer, True, True, LEADER_TIMEOUT)
    else:
        print("No winner")

def addCandidate(_term, _candidate):
    global term, candidates, vote
    if _term > term:
        term = _term
        candidates = _candidate
        # print("New candidates ", candidates)
        vote = candidates[randint(0, len(candidates) - 1)]
    print("Vote", vote)
    return vote

def runTimer():
    global leader
    # print(leader, selfId, not leader or leader != selfId)
    if not leader or leader != selfId:
        startElection()
        return
    if leader == selfId:
        sendHeartbeat()
       

def sendHeartbeat():
    global commited
    print("Send heartbeat")
    nodes = getNodes()
    for id in nodes:
        if id != selfId:
            try:
                # print("Send heartbeat to ", id)
                nodes[id].receiveHeartbeat(selfId, term, commited)
            except:
                print("Error ", id, " didn't answer")

timer = None
def startTimer():
    global timer
    # print("Start timer")
    timer = MyTimer(runTimer)
    if AUTO_LEADER == selfId:
        runTimer()

startTimer()

server.requestLoop()