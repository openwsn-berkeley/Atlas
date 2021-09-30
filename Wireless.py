# built-in
import abc
import sys
import random
import numpy as np
# local
import Utils as u

from statistics import mode
from statistics import mean

# TODO: Add timing infrastructure to all these

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
    
    def receive(self, frame):
        raise SystemError('Abstract class')

class PropagationBase(abc.ABC):
    '''
    Communications model.

    Base class. Fully connected.
    '''
    def __init__(self, *args, **kwargs):
        pass

    def getPDR(self, sender_loc, receiver_loc, **kwargs):
        return 1

class PropagationLOS(PropagationBase):
    raise NotImplementedError()

class PropagationRadius(PropagationBase):
    raise NotImplementedError()

class PropagationFriis(PropagationBase):
    '''
    Communications model.

    Classic Friis Path Loss Model: https://www.gaussianwaves.com/2013/09/friss-free-space-propagation-model/
    '''
    TWO_DOT_FOUR_GHZ = 2400000000  # Hz
    SPEED_OF_LIGHT = 299792458  # m/s

    # RSSI and PDR relationship obtained by experiment; dataset was available
    # at the link shown below:
    # http://wsn.eecs.berkeley.edu/connectivity/?dataset=dust
    RSSI_PDR_TABLE = {
        -97: 0.0000,  # this value is not from experiment
        -96: 0.1494,
        -95: 0.2340,
        -94: 0.4071,
        # <-- 50% PDR is here, at RSSI=-93.6
        -93: 0.6359,
        -92: 0.6866,
        -91: 0.7476,
        -90: 0.8603,
        -89: 0.8702,
        -88: 0.9324,
        -87: 0.9427,
        -86: 0.9562,
        -85: 0.9611,
        -84: 0.9739,
        -83: 0.9745,
        -82: 0.9844,
        -81: 0.9854,
        -80: 0.9903,
        -79: 1.0000,  # this value is not from experiment
    }

    TX_POWER = 0
    ANTENNA_GAIN = 0  # TX & RX

    # TODO: add a loss parameter (alpha=0, dB_loss=0)

    def _friisModel(self, distance):
        # sqrt and inverse of the free space path loss (fspl)
        free_space_path_loss = (
                self.SPEED_OF_LIGHT / (4 * np.pi * distance * self.TWO_DOT_FOUR_GHZ)
        )

        # simple friis equation in Pr = Pt + Gt + Gr + 20log10(fspl)
        rssi = (
                self.TX_POWER +
                self.ANTENNA_GAIN +  # tx
                self.ANTENNA_GAIN +  # rx
                (20 * np.log10(free_space_path_loss))
        )

        return rssi

    def _rssi_to_pdr(self, rssi):
        minRssi = min(self.RSSI_PDR_TABLE.keys())
        maxRssi = max(self.RSSI_PDR_TABLE.keys())

        if rssi < minRssi:
            pdr = 0.0
        elif rssi > maxRssi:
            pdr = 1.0
        else:
            floor_rssi = int(np.floor(rssi))
            pdr_low = self.RSSI_PDR_TABLE[floor_rssi]
            pdr_high = self.RSSI_PDR_TABLE[floor_rssi + 1]
            # linear interpolation
            pdr = (pdr_high - pdr_low) * (rssi - float(floor_rssi)) + pdr_low

        assert pdr >= 0.0
        assert pdr <= 1.0

        return pdr

class PropagationPister(PropagationFriis):
    '''
    Communications model.

    Pister Hack or Experimental Randomness variant.
    '''

    PISTER_HACK_LOWER_SHIFT = 40  # dB

    def getPDR(self, sender_loc, receiver_loc, **kwargs):
        '''
        Pister Hack model for PDR calculation based on distance/ signal attenuation
        '''
        distance = u.distance(sender_loc, receiver_loc)
        if distance == 0:
            return 1

        rssi = self._friisModel(distance) - random.uniform(0, self.PISTER_HACK_LOWER_SHIFT)
        pdr = self._rssi_to_pdr(rssi)

        return pdr

class WirelessBase(abc.ABC):
    '''
    The wireless medium through which DotBot and orchestrator communicate.

    Note: Not thread-safe.
    '''
    DFLT_PDR = 1.0

    # singleton pattern
    _instance = None
    _init = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(WirelessBase, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, propagation=PropagationBase):

        # singleton patterm
        # if instance of class already exists the return, to restrict to one instance only
        if self._init:
            return
        self._init = True

        # store params
        self.devices = []
        self.lastLinks = None
        self.lastLinkPDRs = None
        self.lastTree = None
        self.lastNodes = None
        self.currentPDR = None
        self.propagation = propagation()

        # TODO: PDR Matrix store

        # local variables

    # ======================== public ==========================================

    def indicateDevices(self, devices):
        """
        Indicates devices available for transmission.
        """
        self.devices = devices # TODO: make this a set
        #        self.createPDRmatrix(devices)
        self.orch = self.devices[-1]

    def destroy(self):
        """
        Singleton destructor.
        """
        self._instance = None
        self._init = False

    def transmit(self, frame, sender: WirelessDevice, receiver_filter: set = None):

        assert self.devices  # make sure there are devices

        for receiver in self.devices:
            if receiver == sender or \
                    (receiver_filter is not None and receiver not in receiver_filter):
                continue  # ensures transmitter doesn't receive
            pdr = self._computePDR(sender, receiver)
            rand = random.uniform(0, 1)
            if rand < pdr:
                receiver.receive(frame)

    # ======================== private =========================================

    def _computePDR(self, sender, receiver):
        return self._getPDR(sender, receiver)

    def _getPDR(self, sender, receiver, **kwargs):
        """
        Abstract method for PDR calculation for a given communications model.
        """
        # TODO: DotBot class that stores position as np array and can compute distance like that
        assert sender != receiver

        if sender == self.orch and receiver != self.orch:
            sender_loc = self.orch.initialPosition
            receiver_loc = receiver.computeCurrentPosition()
        elif receiver == self.orch and sender != self.orch:
            receiver_loc = self.orch.initialPosition
            sender_loc = sender.computeCurrentPosition()
        else:
            sender_loc = sender.computeCurrentPosition()
            receiver_loc = receiver.computeCurrentPosition()

        distance = u.distance(sender_loc, receiver_loc)
        if distance == 0:
            return 1

        return self.propagation.getPDR(sender_loc, receiver_loc, **kwargs)

class WirelessConcurrentTransmission(WirelessBase):
    """
    Communications model for concurrent transmission.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise NotImplementedError("Concurrent transmission not currently implemented.")

    def _computePDR(self, sender, receiver):
        links = {}
        newLinks = {}
        treeInput = None

        if sender == self.orch:
            movingNode = receiver
        else:
            movingNode = sender

        allDotBots = self.devices.copy()
        allDotBots.pop()
        allRelays = [d for d in allDotBots if d.dotBotId in self.orch.navigation.readyRelays.copy()]

        allNodes = [self.orch] + allRelays + [movingNode]

        if not allRelays:
            pdr = self._getPDR(sender, receiver)
            self.currentPDR = pdr
            return pdr

        for node1 in allNodes:
            for node2 in allNodes:
                if node2 == node1:
                    continue

                linkPDR = self._getPDR(node1, node2)

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

        if self.lastLinks == links:
            allPDRs = self.lastLinkPDRs
        else:
            CToutput = self._computeSuccess(links, treeInput, newLinks)
            allPDRs = CToutput[0]
            self.lastTree = CToutput[1]

        self.lastLinks = links
        self.lastLinkPDRs = allPDRs
        self.lastNodes = allNodes

        pdr = [sp[1] for sp in allPDRs.items() if sp[0] == movingNode]

        if pdr:
            self.currentPDR = pdr[0]
            return pdr[0]

        else:
            return 1

    def _computeSuccess(self, *args, **kwargs):
        raise NotImplementedError()



