# built-in
import abc
import random
# built-in
import numpy as np
# local
import Utils as u

# setup logging
import logging.config
import LoggingConfig
logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)
log = logging.getLogger('Wireless')

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

class PropagationPisterHack(PropagationBase):
    '''
    Communications model.

    Pister Hack or Experimental Randomness variant.
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

    PISTER_HACK_LOWER_SHIFT = 40  # dB

    def getPDR(self, sender_loc, receiver_loc, **kwargs):
        '''
        Pister Hack model for PDR calculation based on distance/ signal attenuation
        '''
        distance = u.distance(sender_loc, receiver_loc)
        if distance == 0:
            return 1

        shift_value = random.uniform(0, self.PISTER_HACK_LOWER_SHIFT)

        rssi = self._friisModel(distance) - shift_value
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

    def __init__(self, propagation=PropagationPisterHack):

        # singleton pattern
        # if instance of class already exists the return, to restrict to one instance only
        if self._init:
            return
        self._init = True

        # store params
        self.devices = []
        self.lastTree = None
        self.last_num_relays = 0
        self.edge_node_pdrs = None
        self.currentPDR = None
        self.propagation = propagation()
        self.pdrs = []

        # local variables

    # ======================== public ==========================================

    def indicateDevices(self, devices):
        """
        Indicates devices available for transmission.
        """
        self.devices = devices
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
        self.all_robot_pdrs = set()
        for receiver in self.devices:
            if receiver == sender or \
                    (receiver_filter is not None and receiver not in receiver_filter):
                continue  # ensures transmitter doesn't receive
            pdr = self._computePDR(sender, receiver)
            if sender == self.orch:
                robot = receiver
            else:
                robot = sender
            self.all_robot_pdrs.add((robot.dotBotId,robot.computeCurrentPosition(),pdr, robot.relay))
            rand = random.uniform(0, 1)

            if rand < pdr:
                receiver.receive(frame)
        self.pdrs=list(self.all_robot_pdrs)

    def getPdr(self):
        return self.pdrs

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

        new_relay = allNodes[-1]

        num_relays = len(allRelays) if allRelays else 0
        allNodes.append("moving node")

        if num_relays > self.last_num_relays:
            tree = self._updateTree(self.orch, allNodes, self.lastTree, new_relay)
        else:
            tree = self.lastTree

        CToutput = self._computeSuccess(tree, movingNode, num_relays)
        allPDRs = CToutput

        self.lastTree = tree
        self.last_num_relays = num_relays

        return   allPDRs["moving node"]

    def _computeSuccess(self, tree, moving_node,num_relays, *args, **kwargs):

        if num_relays > self.last_num_relays:
            recomputed_pdrs = self._recomputeAllPDRs(tree, moving_node)
            node_pdrs       = recomputed_pdrs[0]
            self.last_pdrs  = node_pdrs
            self.edge_node_pdrs  = recomputed_pdrs[1]
        else:
            node_pdrs = self._updateNodesPDR(tree, self.last_pdrs, moving_node, self.edge_node_pdrs)

        sp = self._findSuccessProbability(node_pdrs)

        return sp

    def _updateTree(self,root_node, all_nodes, last_tree, new_relay):
        # need to evaluate how many branches need to branch out from this one
        # add new branch to branches to be extended if current node != moving node
        # once all possible extensions have been added pop from branches to be extended
        # until we no longer have branches to be extended

        if last_tree:
            current_tree = last_tree
        else:
            current_tree = [[root_node, "moving node"]]

        branches_to_extend = [branch[0:-1] + [new_relay] for branch in current_tree]

        idx = 0
        while branches_to_extend:
            branch = branches_to_extend[idx]
            extension_nodes = set(all_nodes) - set(branch)
            for node in extension_nodes:
                if node != "moving node":
                    branches_to_extend.append(branch + [node])
                else:
                    current_tree.append(branch + [node])
                    branches_to_extend.remove(branch)

        return current_tree

    def _updateNodesPDR(self, tree, last_pdrs, moving_node, edge_node_pdrs):
        # for every edge node, find pdr with moving node then multiply by edge connecting node pdr
        # remove the final entry from node pdrs and replace with new entry for this moving node
        # the finding success probability will be done in the same way

        node_pdrs = last_pdrs
        node_pdrs["moving node"] = []
        for node in edge_node_pdrs:
            if node[0] == "moving node" or node[0] == moving_node:
                continue
            link_pdr = self._getPDR(node[0],moving_node)
            node_pdrs["moving node"].append(link_pdr * node[1])

        return node_pdrs

    def _recomputeAllPDRs(self, tree, moving_node):

        root = tree[0][0]
        node_pdrs = {root: [1]}
        edge_nodes = []

        for branch in tree:
            pdr_of_previous_node = 1
            for i in range(len(branch) - 1):
                if branch[i+1] == "moving node":
                    next_node = moving_node
                else:
                    next_node = branch[i+1]
                if branch[i] == next_node:
                    continue
                link_pdr = self._getPDR(branch[i], next_node)
                if str(branch[i + 1]) not in node_pdrs.keys():
                    node_pdrs[str(branch[i + 1])] = []
                node_pdr = round(link_pdr * pdr_of_previous_node, 4)
                node_pdrs[str(branch[i + 1])] += [node_pdr]
                if branch[i] == branch[-2]:
                    edge_nodes.append((branch[i],pdr_of_previous_node))
                pdr_of_previous_node = node_pdr

        return node_pdrs, edge_nodes

    def _findSuccessProbability(self, node_pdrs):
        nodes = node_pdrs.keys()
        final_pdrs = {}

        for node in nodes:
            failure_probability = round(np.prod([1 - node_pdr for node_pdr in list(set(node_pdrs[node]))]), 4)
            success_probability = 1 - failure_probability
            final_pdrs[node] = success_probability

        return final_pdrs




