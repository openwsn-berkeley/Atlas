# built-in
import random
import numpy as np
# third-party
# local
import Utils as u
import computeSuccess

from statistics import mode
from statistics import mean

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
        self.pdrs            = []
        self.lastLinks       = None
        self.lastLinkPDRs    = None
        self.lastTree        = None
        self.lastNodes       = None
        self.currentPDR      = None


        # local variables

    # ======================== public ==========================================
    
    def indicateDevices(self,devices):
        self.devices                 = devices
#        self.createPDRmatrix(devices)
        self.orch                    = self.devices[-1]

    def overridePDR(self,pdr):
        self.constantPDR             = pdr

    def destroy(self): 
        self._instance       = None
        self._init           = False

    def pdrMode(self):
        #Mode = min(set(self.pdrs), key=self.pdrs.count)
        #Mode = mode(self.pdrs)
        arg = mean(self.pdrs)
        self.pdrs = []
        return arg

    def transmit(self, frame, sender):

        assert self.devices # make sure there are devices

        for receiver in self.devices:
            if receiver==sender:
                continue # ensures transmitter doesn't receive
            #pdr  = self._computePDR(sender,receiver)
            pdr = 1
            self.pdrs += [pdr]
            rand = random.uniform(0,1)
            if rand<pdr:
                receiver.receive(frame)
            else:
                pass

    # ======================== private =========================================

    PISTER_HACK_LOWER_SHIFT  =         40 # dB
    TWO_DOT_FOUR_GHZ         = 2400000000 # Hz
    SPEED_OF_LIGHT           =  299792458 # m/s

    # RSSI and PDR relationship obtained by experiment; dataset was available
    # at the link shown below:
    # http://wsn.eecs.berkeley.edu/connectivity/?dataset=dust
    RSSI_PDR_TABLE = {
        -97:    0.0000,  # this value is not from experiment
        -96:    0.1494,
        -95:    0.2340,
        -94:    0.4071,
        # <-- 50% PDR is here, at RSSI=-93.6
        -93:    0.6359,
        -92:    0.6866,
        -91:    0.7476,
        -90:    0.8603,
        -89:    0.8702,
        -88:    0.9324,
        -87:    0.9427,
        -86:    0.9562,
        -85:    0.9611,
        -84:    0.9739,
        -83:    0.9745,
        -82:    0.9844,
        -81:    0.9854,
        -80:    0.9903,
        -79:    1.0000,  # this value is not from experiment
    }

    TX_POWER = 0
    ANTENNA_GAIN = 0 # TX & RX

    def _computePDR(self, sender, receiver):

        links     = {}
        newLinks  = {}
        treeInput = None

        if sender == self.orch:
            movingNode = receiver
        else:
            movingNode = sender

        allDotBots = self.devices.copy()
        allDotBots.pop()
        allRelays = [d for d in allDotBots if d.dotBotId in self.orch.navigation.readyRelays.copy()]

        allNodes  = [self.orch] + allRelays + [movingNode]

        if not allRelays:
            pdr = self._getPisterHackPDR(sender,receiver)
            self.currentPDR = pdr
            return pdr


        for node1 in allNodes:
            for node2 in allNodes:
                if node2 == node1:
                    continue

                linkPDR = self._getPisterHackPDR(node1,node2)

                # if linkPDR == 0:
                #     continue

                links[(node1, node2)] = linkPDR


        if self.lastTree:
            treeInput = self.lastTree


        if not self.lastTree:
            newLinks = None
        else:
            for link in links.items():
                if link[0][0] in self.lastNodes:
                    newLinks[link[0]] = link[1]

        if self.lastLinks ==  links:
            allPDRs = self.lastLinkPDRs
        else:
            CToutput      = computeSuccess.computeSuccess(links,  treeInput, newLinks)
            allPDRs       = CToutput[0]
            self.lastTree = CToutput[1]

        self.lastLinks    = links
        self.lastLinkPDRs = allPDRs
        self.lastNodes    = allNodes


        pdr     = [sp[1] for sp in allPDRs.items() if sp[0]==movingNode]

        if pdr:
            self.currentPDR = pdr[0]
            return pdr[0]

        else:
            return 1
    
    def _getPisterHackPDR(self,sender,receiver, rssi=False):
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

        distance = u.distance(pos1, pos2)
        if distance == 0:
            return 1

        res = self._PisterHackModel(distance)

        return res if rssi else res[0]

    def _PisterHackModel(self, distance):
        # sqrt and inverse of the free space path loss (fspl)
        free_space_path_loss = (
            self.SPEED_OF_LIGHT / (4 * np.pi * distance * self.TWO_DOT_FOUR_GHZ)
        )

        # simple friis equation in Pr = Pt + Gt + Gr + 20log10(fspl)
        pr = (
            self.TX_POWER     +
            self.ANTENNA_GAIN + # tx
            self.ANTENNA_GAIN + # rx
            (20 * np.log10(free_space_path_loss))
        )

        rssi = pr - random.uniform(0, self.PISTER_HACK_LOWER_SHIFT)

        minRssi = min(self.RSSI_PDR_TABLE.keys())
        maxRssi = max(self.RSSI_PDR_TABLE.keys())

        if rssi < minRssi:
            pdr = 0.0
        elif rssi > maxRssi:
            pdr = 1.0
        else:
            floor_rssi = int(np.floor(rssi))
            pdr_low    = self.RSSI_PDR_TABLE[floor_rssi]
            pdr_high   = self.RSSI_PDR_TABLE[floor_rssi + 1]
            # linear interpolation
            pdr = (pdr_high - pdr_low) * (rssi - float(floor_rssi)) + pdr_low

        assert pdr >= 0.0
        assert pdr <= 1.0
        
        return pdr, rssi

