# built-in
# third-party
# local
import random


class Wireless(object):
    '''
    The wireless medium through which DotBot and orchestrator communicate.
    '''

    # TODO: change into a PDR table later on

    PDR = 0.5

    # singleton pattern: a python design pattern that restrics the instanciation of class to one object only
    # so that all there is only one global access point to the class instance
    _instance = None
    _init = False

    # magic methods: called when instance of class is created

    # creates instance of class
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Wireless, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):

        # singleton patterm
        # if instance of class already exists the return, to restrict to one instance only
        if self._init:
            return
        self._init = True

        # local variables
        self.dotbots = None
        self.orchestrator = None
        self.packetCounter = 0

    # ======================== public ==========================================

    def indicateElements(self, dotbots, orchestrator):
        assert self.dotbots == None
        assert self.orchestrator == None

        self.dotbots = dotbots
        self.orchestrator = orchestrator

    def toDotBots(self, msg):
        for dotbot in self.dotbots:
            if self.PDR == 1 or self.packetCounter < 3:
                dotbot.fromOrchestrator(msg)
            elif random.randint(0, 1) < self.PDR:
                dotbot.fromOrchestrator(msg)
            else:
                pass
            self.packetCounter += 1

    def toOrchestrator(self, msg):
        if self.PDR == 1:
            self.orchestrator.fromDotBot(msg)
        elif random.randint(0, 1) < self.PDR:
            self.orchestrator.fromDotBot(msg)
        else:
            pass

        self.packetCounter += 1

    # ======================== private =========================================
