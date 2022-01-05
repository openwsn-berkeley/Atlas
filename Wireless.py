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
        #-79: 1.0000,  # this value is not from experiment
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
        self.pdrs = []
        for receiver in self.devices:
            if receiver == sender or \
                    (receiver_filter is not None and receiver not in receiver_filter):
                continue  # ensures transmitter doesn't receive
            pdr = self._computePDR(sender, receiver)
            self.pdrs.append(pdr)
            rand = random.uniform(0, 1)
            if rand < pdr:
                receiver.receive(frame)
        self.getPdrAvg()

    def getPdrAvg(self):
        return sum(self.pdrs)/len(self.pdrs)

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

        allNodes = [self.orch]

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
                allNodes.append(db)

        allNodes.append(movingNode)

        CToutput = self._computeSuccess(all_nodes=allNodes, last_tree=self.lastTree)
        allPDRs = CToutput[0]
        self.lastTree = CToutput[1]

        self.lastNodes = allNodes

        pdr = [sp[1] for sp in allPDRs.items() if sp[0] == str(movingNode)]

        if pdr:
            self.currentPDR = pdr[0]
            return pdr[0]

        else:
            print("NO PDR RETURNED!")
            return 1

    def _computeSuccess(self, all_nodes, last_tree=None, new_nodes=None, *args, **kwargs):
        all_nodes = all_nodes
        root_node = all_nodes.pop(0)

        tree = self._updateTree(root_node=root_node, all_nodes=all_nodes)

        node_pdrs = self._updateNodesPDR(tree)

        sp = self._findSuccessProbability(node_pdrs)

        return (sp, tree)

    def _updateTree(self, root_node, all_nodes):
        extended_tree = self._extendBranches(root_node=root_node, all_nodes=all_nodes)
        return extended_tree

    def _extendBranches(self,root_node, all_nodes):
        existing_branches = self._addRootBranches(root_node, all_nodes)
        updated_branches = []

        i = 0
        while i < len(existing_branches):
            for (idx, node) in enumerate(all_nodes):
                if node in existing_branches[i]:
                    continue

                new_branch = existing_branches[i] + [node]
                if len(new_branch) == (len(all_nodes) + 1):
                    updated_branches.append(new_branch)
                existing_branches.append(new_branch)

            i += 1
        if not updated_branches:
            new_branches = existing_branches
        else:
            new_branches = updated_branches

        return new_branches

    def _addRootBranches(self, root_node, nodes):
        root = root_node
        root_branches = []
        for node in nodes:
            root_branches.append([root, node])

        return root_branches

    def _updateNodesPDR(self, tree):

        root = tree[0][0]
        node_pdrs = {root: [1]}

        for branch in tree:
            pdr_of_previous_node = 1
            for i in range(len(branch) - 1):
                link_pdr = self._getPDR(branch[i], branch[i+1])
                if str(branch[i + 1]) not in node_pdrs.keys():
                    node_pdrs[str(branch[i + 1])] = []
                node_pdr = round(link_pdr * pdr_of_previous_node, 4)
                node_pdrs[str(branch[i + 1])] += [node_pdr]
                pdr_of_previous_node = node_pdr

        return node_pdrs

    def _findSuccessProbability(self, node_pdrs):
        nodes = node_pdrs.keys()
        final_pdrs = {}

        for node in nodes:
            failure_probability = round(np.prod([1 - node_pdr for node_pdr in list(set(node_pdrs[node]))]), 4)
            success_probability = 1 - failure_probability
            final_pdrs[node] = success_probability

        return final_pdrs




