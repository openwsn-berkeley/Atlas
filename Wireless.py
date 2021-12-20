# built-in
import abc
import sys
import random
import time
from functools import wraps
import numpy as np
# local
import Utils as u
from Floorplan import Floorplan

from statistics import mode
from statistics import mean

def timeit(my_func):
    @wraps(my_func)
    def timed(*args, **kw):
        tstart = time.time()
        output = my_func(*args, **kw)
        tend = time.time()
        print('"{}" took {:.3f} s to execute\n'.format(my_func.__name__, (tend - tstart)))
        return output

    return timed

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

    def getPDR(self, sender_loc, receiver_loc, **kwargs):
        return 1

    def indicateFloorplan(self, floorplan):
        pass

class PropagationRadius(PropagationBase):
    '''
    Radius based propagation model.

    Binary and probabilistic.
    '''

    def __init__(self, radius=10):
        self.radius = radius

    def getPDR(self, sender_loc, receiver_loc, **kwargs):
        """
        Return PDR based on radius model
        """
        distance = u.distance(sender_loc, receiver_loc)

        return 1 if distance <= self.radius else 0

class PropagationLOS(PropagationBase):
    """
    Line of Sight propagation model.

    Based on known environment model.
    """

    EPS = 1e-6

    def indicateFloorplan(self, floorplan):
        '''
        Break each floorplan obstacle down to 4 lines.
        '''
        self.floorplan =   floorplan
        self.obstacle_boundaries     = []
        for obstacle in self.floorplan.obstacles:
            ax    = obstacle['x']
            ay    = obstacle['y']
            ow    = obstacle['width']
            oh    = obstacle['height']

            line1 = ((ax,ay), (ax+ow,ay))
            line2 = ((ax,ay+oh), (ax+ow,ay+oh))
            line3 = ((ax,ay), (ax,ay+oh))
            line4 = ((ax+ow,ay), (ax+ow,ay+oh))
            self.obstacle_boundaries += [line1, line2, line3, line4]

    @staticmethod
    def line_intersection(line1, line2):
        '''
        Determine whether 2 lines intersect.

        Note: If intersection is at edge of line1, does not consider lines intersected.

        TODO: fix this to handle same slope intersections
        '''
        line1_x = [line1[0][0], line1[1][0]]
        line1_y = [line1[0][1], line1[1][1]]

        (line1_xmin, line1_xmax) = (min(line1_x), max(line1_x))
        (line1_ymin, line1_ymax) = (min(line1_y) ,max(line1_y))

        line2_x = [line2[0][0], line2[1][0]]
        line2_y = [line2[0][1], line2[1][1]]

        (line2_xmin, line2_xmax) = (min(line2_x), max(line2_x))
        (line2_ymin, line2_ymax) = (min(line2_y), max(line2_y))

        xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
        ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

        def det(a, b):
            return a[0] * b[1] - a[1] * b[0]

        div = det(xdiff, ydiff)

        if div == 0:
            containedX = line1_xmin == line2_xmin == line1_xmax == line2_xmax and line1_ymin <= line2_ymin <= line2_ymax <= line1_ymax
            containedY = line1_ymin == line2_ymin == line1_ymax == line2_ymax and line1_xmin <= line2_xmin <= line2_xmax <= line1_xmax
            return containedX or containedY

        d = (det(*line1), det(*line2))
        xi = det(d, xdiff) / div
        yi = det(d, ydiff) / div

        intersectionL1 = line1_xmin <= xi <= line1_xmax and line1_ymin <= yi <= line1_ymax
        intersectionL2 = line2_xmin <= xi <= line2_xmax and line2_ymin <= yi <= line2_ymax

        corners = any([xi == _x and yi == _y for (_x, _y) in zip(line1_x, line1_y)])

        return intersectionL1 and intersectionL2 and not corners

    def getPDR(self, sender_loc, receiver_loc, **kwargs):
        '''
        Return PDR based on LOS model
        '''
        tx_line = (sender_loc, receiver_loc)

        # loop through obstacles, looking for intersection
        for obstacle_line in self.obstacle_boundaries:
            if self.line_intersection(tx_line, obstacle_line):
                return 0
        return 1

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

    def __init__(self, propagation=PropagationPister):

        # singleton pattern
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
        self.dotbots = self.devices[:-1]

    def indicateFloorplan(self, floorplan):
        self.propagation.indicateFloorplan(floorplan)

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


    def _computePDR(self, sender, receiver):
        links = {}
        newLinks = {}
        treeInput = None
        allNodes = set()

        if sender == self.orch:
            movingNode = receiver
        else:
            movingNode = sender

        allRelays = self.orch.navigation.readyRelays

        if not allRelays:
            pdr = self._getPDR(sender, receiver)
            self.currentPDR = pdr
            return pdr

        # FIXME: can we do this without looping over all robots
        for db in self.dotbots:
            if db.dotBotId in allRelays:
                allNodes.add(db)

        allNodes.add(self.orch)
        allNodes.add(movingNode)
        all_nodes_copy = list(allNodes)

        for (i, node) in enumerate(allNodes):
            nodes_left = all_nodes_copy[i+1:]
            while nodes_left:
                links[(node, nodes_left[0])] = self._getPDR(node, nodes_left[0])
                nodes_left.pop()

        if self.lastTree:
            treeInput = self.lastTree
            for link in links.items():
                if link[0][0] in self.lastNodes:
                    newLinks[link[0]] = link[1]
        else:
            newLinks = None

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

    def _computeSuccess(self, links, lastTree = None, newLinks=None, *args, **kwargs):

        tree = []
        rootBranches = []
        pdrPerNode = {}
        processedRootNodes = []
        sucessProbabilities = {}
        endBranch = False

        sender = (list(links.keys())[0], list(links.values())[0])

        if not lastTree:
            for link in links.items():
                node_1   = link[0][0]
                link_pdr = link[1]
                if node_1 == sender[0][0]:
                    if link_pdr != 0:
                        rootBranches += [link]

            for rb in rootBranches:
                rbExtendedBranch = []
                while True:
                    connectingNode = rb
                    branch = {}
                    branch[rb[0]] = rb[1]
                    idx = 0
                    while idx <= len(rootBranches):
                        for link in links.items():

                            if link[0] in rbExtendedBranch:
                                continue
                            if link[0] in branch.keys():
                                continue
                            if link[0][1] == connectingNode[0][0]:
                                continue
                            if link[0][1] in [b[0] for b in branch.keys()]:
                                continue
                            if link[0][0] == connectingNode[0][1]:
                                connectingNode = link
                                branch[link[0]] = link[1]
                                break
                        idx += 1
                    if branch == {rb[0]: rb[1]} or endBranch:
                        endBranch = False
                        break
                    else:
                        tree += [branch]
                        rbExtendedBranch += branch
        elif newLinks:
            for rb in lastTree:
                rbExtendedBranch = set()
                while True:
                    connectingNode = (list(rb.keys())[0], list(rb.values())[0])
                    branch = rb
                    idx = 0
                    while idx <= len(rootBranches):
                        for link in newLinks.items():

                            if link[0] in rbExtendedBranch:
                                continue
                            if link[0] in branch.keys():
                                continue
                            if link[0][1] == connectingNode[0][0]:
                                continue
                            if link[0][1] in [b[0] for b in branch.keys()]:
                                continue
                            if link[0][0] == connectingNode[0][1]:
                                connectingNode = link
                                branch[link[0]] = link[1]
                                break
                        idx += 1
                    if branch == rb or endBranch:
                        endBranch = False
                        break
                    else:
                        tree += [branch]
                        rbExtendedBranch.add(branch)
        else:
            tree = lastTree

        for b in tree:

            pdr = 1
            pdrPerNode[sender[0][0]] = [pdr]

            for node in b.items():

                pdr = pdr * node[1]

                if node in processedRootNodes:
                    continue

                if node[0][0] == sender[0][0]:
                    processedRootNodes += [node]

                if node[0][1] not in pdrPerNode.keys():
                    pdrPerNode[node[0][1]] = [round(pdr, 4)]
                else:
                    pdrPerNode[node[0][1]] += [round(pdr, 4)]

        for node in pdrPerNode.items():
            failureProbability = 1
            for pdr in node[1]:
                failureProbability = failureProbability * (1 - round(pdr, 4))
            successProbability = 1 - failureProbability
            sucessProbabilities[node[0]] = round(successProbability, 4)

        return [sucessProbabilities, tree]



