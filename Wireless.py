# built-in
import random
import math
# built-in
# third-party
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

class Wireless(object):
    '''
    The wireless medium through which DotBot and orchestrator communicate.

    Note: Not thread-safe.
    '''

    DFLT_PDR           = 1

    TWO_DOT_FOUR_GHZ   = 2400000000    # Hz
    SPEED_OF_LIGHT     = 299792458     # m/s

    # RSSI and PDR relationship obtained by experiment; dataset was available
    # at the link shown below:
    # http://wsn.eecs.berkeley.edu/connectivity/?dataset=dust
    RSSI_PDR_TABLE     = {
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

    TX_POWER                = 0
    ANTENNA_GAIN            = 0   # TX & RX

    PISTER_HACK_LOWER_SHIFT = 40  # dB

    # singleton pattern
    _instance        = None
    _init            = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Wireless, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):

        # singleton pattern
        # if instance of class already exists the return, to restrict to one instance only
        if self._init:
            return
        self._init = True
        
        # local variables
        self.devices        = []
        self.lastRelays     = []
        self.lastTree       = None
        self.last_pdrs      = None
        self.edge_node_pdrs = None
    # ======================== public ==========================================

    def indicateDevices(self, devices):
        """
        Indicates devices available for transmission.
        """
        self.devices = devices

    def destroy(self):
        """
        Singleton destructor.
        """
        self._instance = None
        self._init = False

    def transmit(self, sender, frame):
        for receiver in self.devices:

            if receiver == sender:
                continue  # transmitter doesn't receive

            assert sender != receiver

            pdr            = self._computeConcurrentTransmissionPDR(sender, receiver)
            log.debug(f'PDR between {sender} and {receiver} is {pdr}')

            if random.uniform(0, 1) < pdr:
                receiver.receive(frame)

    # ======================== private =========================================

    def _computePdrPisterHack(self, sender_pos, receiver_pos):
        '''
        Pister Hack model for PDR calculation based on distance/ signal attenuation
        '''

        distance    = u.distance(sender_pos, receiver_pos)

        shift_value = random.uniform(0, self.PISTER_HACK_LOWER_SHIFT)
        rssi        = self._friisModel(distance) - shift_value
        pdr         = self._rssi_to_pdr(rssi)

        return pdr

    def _friisModel(self, distance):

        # sqrt and inverse of the free space path loss (fspl)
        free_space_path_loss = (
                self.SPEED_OF_LIGHT / (4 * math.pi * distance * self.TWO_DOT_FOUR_GHZ)
        )

        # simple friis equation in Pr = Pt + Gt + Gr + 20log10(free_space_path_loss)
        rssi = (
                self.TX_POWER     +
                self.ANTENNA_GAIN +  # tx
                self.ANTENNA_GAIN +  # rx
                (20 * math.log10(free_space_path_loss))
        )

        return rssi

    def _rssi_to_pdr(self, rssi):

        if rssi < min(self.RSSI_PDR_TABLE.keys()):
            pdr = 0.0
        elif rssi > max(self.RSSI_PDR_TABLE.keys()):
            pdr = 1.0
        else:
            floor_rssi = int(math.floor(rssi))
            pdr_low    = self.RSSI_PDR_TABLE[floor_rssi]
            pdr_high   = self.RSSI_PDR_TABLE[floor_rssi + 1]
            # linear interpolation
            pdr        = (pdr_high - pdr_low) * (rssi - float(floor_rssi)) + pdr_low

        assert pdr >= 0.0
        assert pdr <= 1.0

        return pdr

    def _computeConcurrentTransmissionPDR(self, sender, receiver):

        # orchestrator is always root node, PDR = 1 always
        rootNode = self.devices[-1]

        # check which of the two given nodes is the moving Node
        for device in [sender, receiver]:
            if device != rootNode:
                movingNode = device

        # check which devices are relay nodes
        relays = []
        for device in self.devices[0:-1]:
            if device.relay == True:
                relays += [device]

        # if no relays yet, get PDR through Pister-Hack
        if not relays:
            return self._computePdrPisterHack(
                sender_pos   = sender.computeCurrentPosition(),
                receiver_pos = receiver.computeCurrentPosition()
             )

        nodes = [rootNode] + relays + [movingNode]

        if relays != self.lastRelays:
            # update tree of nodes
            tree = self._updateTree(
                nodes    = nodes,
                lastTree = self.lastTree,
                newRelay = list(set(relays).difference(set(self.lastRelays)))[0]
            )
        else:
            # use last tree since all nodes are the same
            tree = self.lastTree

        sp = self._computeSuccessProbabilityCT(tree, nodes)

        # store current relays and last tree
        self.lastRelays = relays
        self.lastTree   = tree

        return sp

    def _updateTree(self,nodes, lastTree, newRelay):

        rootNode   = nodes[0]
        movingNode = nodes[-1]

        if lastTree:
            currentTree = lastTree
        else:
            # add branch of direct connection between root node and moving node
            currentTree = [[rootNode, movingNode]]

        # if we already have a tree take all the same branches except for the last moving node
        # add the new relay and continue extending tree from there
        # then keep expanding each branch from new relay up to moving node

        branches_to_extend = [branch[0:-1] + [newRelay] for branch in currentTree]

        idx = 0
        while branches_to_extend:
            branch          = branches_to_extend[idx]
            extension_nodes = list(set(nodes).difference(set(branch)))
            for node in extension_nodes:
                if node != nodes[-1]:
                    branches_to_extend += [branch + [node]]
                else:
                    currentTree        += [branch + [node]]
                    branches_to_extend.remove(branch)

        return currentTree

    def _computeSuccessProbabilityCT(self, tree, nodes):
        movingNode = nodes[-1]

        if nodes[1:-1] != self.lastRelays:
            # current relays are not the same as last relays
            (node_pdrs, self.edge_node_pdrs)  = self._recomputeAllPDRs(tree, movingNode)
            self.last_pdrs                    = node_pdrs
        else:
            node_pdrs = self._updateNodesPDR(
                tree           = tree,
                last_pdrs      = self.last_pdrs,
                movingNode     = nodes[-1],
                edge_node_pdrs = self.edge_node_pdrs
            )

        nodes = node_pdrs.keys()
        final_pdrs = {}

        for node in nodes:
            failure_probability = round(np.prod([1 - node_pdr for node_pdr in list(set(node_pdrs[node]))]), 4)
            success_probability = 1 - failure_probability
            final_pdrs[node]    = success_probability

        return final_pdrs[str(movingNode)]  # overall PDR of moving node through CT

    def _updateNodesPDR(self, tree, last_pdrs, movingNode, edge_node_pdrs):
        # for every edge node, find pdr with moving node then multiply by edge connecting node pdr
        # remove the final entry from node pdrs and replace with new entry for this moving node
        # the finding success probability will be done in the same way

        node_pdrs                  = last_pdrs
        node_pdrs[str(movingNode)] = []
        for node in edge_node_pdrs:
            if node[0] == str(movingNode) or node[0] == movingNode:
                continue
            link_pdr = self._computePdrPisterHack(node[0].computeCurrentPosition(),movingNode.computeCurrentPosition())
            node_pdrs[str(movingNode)].append(link_pdr * node[1])

        return node_pdrs

    def _recomputeAllPDRs(self, tree, movingNode):

        # root is first link in first branch of tree
        root       = tree[0][0]
        node_pdrs  = {root: [1]}
        edge_nodes = []

        # recompute PDR between all links in tree
        for branch in tree:
            pdr_of_previous_node = 1     # first link in branch is always connected to root (orchestrator)

            for i in range(len(branch) - 1):

                assert branch[i] != branch[i+1]

                # find the PDR of the link between the two nodes
                link_pdr = self._computePdrPisterHack(
                    sender_pos   = branch[i].computeCurrentPosition(),    # node in link closer to root
                    receiver_pos = branch[i+1].computeCurrentPosition()   # node in link closer to moving node
                )

                if str(branch[i+1]) not in node_pdrs.keys():
                    node_pdrs[str(branch[i+1])] = []

                # node PDR = link PDR * PDR of previous node (node closer to root node)
                node_pdr = round(link_pdr * pdr_of_previous_node, 4)
                node_pdrs[str(branch[i+1])] += [node_pdr]

                # this is the edge node connected to the moving node
                if branch[i] == branch[-2]:
                    edge_nodes.append((branch[i], pdr_of_previous_node))

                pdr_of_previous_node = node_pdr

        return node_pdrs, edge_nodes

