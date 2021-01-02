# built-in
# third-party
# local
import random
import Utils as u


class Wireless(object):
    '''
    The wireless medium through which DotBot and orchestrator communicate.
    '''

    # TODO: change into a PDR table later on

    #PDR = 0.7

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
        self.orchX = None
        self.orchY = None
        self.packetCounter = 0
        self.PDR = 1

    # ======================== public ==========================================
    def reset(self,pdr):
        self.packetCounter = 0
        self.PDR = pdr

    def indicateElements(self, dotbots, orchestrator):
        assert self.dotbots == None
        assert self.orchestrator == None

        self.dotbots = dotbots
        self.orchestrator = orchestrator

    def indicateOrchLocation(self, xo, yo):
        #assert self.orchX == None
        #assert self.orchY == None

        self.orchX = xo
        self.orchY = yo

    def toDotBots(self, msg):
        for dotbot in self.dotbots:
            PDR = self.PDR
            if PDR == 1 :
                dotbot.fromOrchestrator(msg)
            elif random.randint(0, 1) < PDR:
                dotbot.fromOrchestrator(msg)
            else:
                pass
            self.packetCounter += 1

    def toOrchestrator(self, msg):
        PDR = self.PDR
        if PDR == 1:
            self.orchestrator.fromDotBot(msg)
        elif random.randint(0, 1) < PDR :
            self.orchestrator.fromDotBot(msg)
        else:
            pass
        self.packetCounter += 1

    # ======================== private =========================================

    def _get_pisterHack_PDR(self,dotbot):
        # if self.packetCounter == 0:
        #     dotbotX = self.orchX
        #     dotbotY = self.orchY
        # else:
        #     dotbotAttitude = dotbot.getAttitude()
        #     dotbotX = dotbotAttitude['x']
        #     dotbotY = dotbotAttitude['y']
        #
        # distance = int(u.distance((dotbotX,dotbotY),(self.orchX,self.orchY)))
        # distanceToPDR = {
        #                 '23': 0.0001, '22': 0.0001, '21': 0.0001, '20': 0.0001, '19': 0.0001,
        #                 '18': 0.0001, '17': 0.1494, '16': 0.2340, '15': 0.4071, '14': 0.6359,
        #                 '13': 0.6866, '12': 0.7476, '11':0.8603, '10': 0.8702, '9':   0.9324,
        #                 '8': 0.9427 , '7': 0.9562, '6': 0.9611, '5': 0.9739, '4': 0.9745,
        #                 '3': 0.9844, '2': 0.9854, '1': 0.9903, '0': 1.0000,
        #                 }
        # PDR = distanceToPDR[str(distance)]
        PDR = 0.8

        return PDR
