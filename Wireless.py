# built-in
import random
# third-party
# local
import Utils as u

class WirelessDevice(object):
    '''
    Abstract class for any device communicating over the wireless medium.
    '''
    COMMANDSIZE            = 30
    FRAMETYPE_COMMAND      = 'command'
    FRAMETYPE_NOTIFICATION = 'notification'
    FRAMETYPE_ALL          = [
        FRAMETYPE_COMMAND,
        FRAMETYPE_NOTIFICATION,
    ]
    
    def receive(self,frame):
        raise SystemError('Abstract class')
    
class Wireless(object):
    '''
    The wireless medium through which DotBot and orchestrator communicate.
    '''

    DFLT_PDR = 1.0
    
    # singleton pattern
    _instance = None
    _init = False
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

        # store params
        self.devices         =  []
        self.constantPDR     =  self.DFLT_PDR
        self.pdrMatrix       = []

        # local variables

    # ======================== public ==========================================
    
    def indicateDevices(self,devices):
        self.devices                 = devices
#        self.createPDRmatrix(devices)
        self.orch                    = self.devices[-1]

    # def createPDRmatrix(self,devices):
    #     for device1 in devices:
    #         for device2 in devices:
    #             if device1 != device2:
    #                 self.pdrMatrix += [(device1,device2, self.constantPDR)]
    #
    # def updatePDRmatrix(self):
    #     for (idx,value) in enumerate(self.pdrMatrix):
    #         if value[0] not in self.orch.navigation.relayBots and value[0] not in self.orch.navigation.relayBots:
    #             continue
    #         newPdr              = self._computePDR(value[0], value[1])
    #         self.pdrMatrix[idx] = (value[0], value[1],newPdr)

    def overridePDR(self,pdr):
        self.constantPDR             = pdr

    def destroy(self): 
        self._instance       = None
        self._init           = False

    def transmit(self, frame, sender):
        assert self.devices # make sure there are devices
        #self.updatePDRmatrix()
        for receiver in self.devices:
            if receiver==sender:
                continue # ensures transmitter doesn't receive
            pdr  = self._computePDR(sender,receiver)
            rand = random.uniform(0,1)
            if rand<pdr:
                receiver.receive(frame)
            else:
                pass

    # ======================== private =========================================

    def _computePDR(self,sender,receiver):

        pdr = self._getPisterHackPDR(sender, receiver)
        rand = random.uniform(0, 1)
        if rand <= pdr:
            #print('real PDR = ', pdr)
            return pdr

        else:
            for relay in self.orch.navigation.readyRelays:
                allDevices = self.devices.copy()
                allDevices.pop()
                relayBot = [device for device in allDevices if device.dotBotId == relay['ID']]
                if relayBot:
                    pdrSenderRelay   = self._getPisterHackPDR(sender,relayBot[0])
                    pdrRelayReceiver = self._getPisterHackPDR(relayBot[0],receiver)
                    pdr = pdrSenderRelay * pdrRelayReceiver
                    rand = random.uniform(0, 1)
                    if rand <= pdr:
                        #print('real PDR = ', pdr)
                        return pdr
                    else:
                        remainingRelays = self.orch.navigation.relayBots.copy()
                        remainingRelays.pop(0)
                        for relay2 in remainingRelays:
                            allDevices = self.devices.copy()
                            allDevices.pop()
                            relayBot2 = [device for device in allDevices if device.dotBotId == relay2['ID']]
                            if relayBot2:
                                pdrSenderRelay = self._getPisterHackPDR(sender, relayBot[0])
                                pdrRelayRelay = self._getPisterHackPDR(relayBot[0], relayBot2[0])
                                pdrRelayReceiver = self._getPisterHackPDR(relayBot2[0], receiver)
                                pdr = pdrSenderRelay * pdrRelayRelay * pdrRelayReceiver
                                rand = random.uniform(0, 1)
                                if rand <= pdr:
                                    #print('real PDR = ', pdr)
                                    return pdr



        return pdr
    
    def _getPisterHackPDR(self,sender,receiver):
        '''
        Pister Hack model for PDR calculation based on distance/ signal attenuation
        '''

        if sender == self.orch and receiver != self.orch:
            pos1 = self.orch.initialPosition
            pos2 = receiver.computeCurrentPosition()
        elif receiver == self.orch and sender != self.orch:
            pos2 = receiver.initialPosition
            pos1 = sender.computeCurrentPosition()
        elif (sender != self.orch and receiver != self.orch):
            pos1 = sender.computeCurrentPosition()
            pos2 = receiver.computeCurrentPosition()
        else:
            return 1


        distance = int(u.distance(pos1,pos2))
        distanceToPDR = [1.0000,0.999,0.999,
                         0.9854,0.9851,0.9848,
                         0.9745,0.9739,0.9737,
                         0.9735,0.9731,0.9730,
                         0.9611,0.9609,0.9605,
                         0.9562,0.9558,0.9555,
                         0.9427,0.9405,0.9400,
                         0.9324,0.8900,0.8800,
                         0.8702,0.8690,0.8680,
                         0.8603,0.8590,0.8580,
                         0.7476,0.7400,0.7300,
                         0.6866,0.6860,0.6700,
                         0.6359,0.6100,0.5200,
                         0.4071,0.3500,0.3200,
                         0.2340,0.2200,0.2100,
                         0.1494,0.1400,0.1300,
                         0.1010,0.1009,0.10003,

                        ]
        # distanceToPDR = [1.0000,0.999,
        #                  0.9854,0.9851,
        #                  0.9745,0.9739,
        #                  0.9735,0.9731,
        #                  0.9611,0.9609,
        #                  0.8702,0.8690,
        #                  0.8603,0.8590,
        #                  0.7476,0.7400,
        #                  0.6866,0.6860,
        #                  0.4071,0.3500,
        #                  0.2340,0.2200,
        #                  0.1494,0.1400,
        #                  0.1010,0.1009,
        #
        #                 ]

        if distance < 50:
            pdr = distanceToPDR[distance]
        else:
            pdr = 0
        return pdr
