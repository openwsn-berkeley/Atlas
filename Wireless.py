# built-in
import random
import math
# built-in
# third-party
import numpy as np
# local
import Utils as u
import DataCollector

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
        self.dataCollector  = DataCollector.DataCollector()
        self.devices        = []
        self.lastRelays     = []
        self.lastTree       = None
        self.lastNodePdrs   = None
        self.edge_nodePdrs  = None
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

    def _computePdrPisterHack(self, sender, receiver):
        '''
        Pister Hack model for PDR calculation based on distance/ signal attenuation
        '''

        distance    = u.distance(sender.computeCurrentPosition(), receiver.computeCurrentPosition())

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
        self.rootNode = self.devices[-1]

        # check which of the two given nodes is the moving Node
        for device in [sender, receiver]:
            if device != self.rootNode:
                movingNode = device

        # check which devices are relay nodes
        relays = []
        for device in self.devices:
            if device == self.rootNode:
                continue     # not a dotBot

            if device.isRelay == True:
                relays += [device]

        if relays:
            # find PDR though CT computations
            pdr = self._getPdrCT(relays, movingNode)

        else:
            # no relays , success probability is link PDR between sender and receiver
            pdr  = self._computePdrPisterHack(
                sender      = sender,
                receiver    = receiver
            )

        self.dataCollector.collect({"type": "DotBot Data", "data": {"PDR": pdr, "dotBotId": movingNode.dotBotId, "isRelay": movingNode.isRelay}})

        assert pdr >= 0.0
        assert pdr <= 1.0

        return pdr

    def _getPdrCT(self, relays, movingNode):

        # update tree of nodes (all possible paths packet could reach sender through )
        tree = self._updateTree(relays, movingNode, self.lastTree) if relays != self.lastRelays else self.lastTree

        # update PDR of all nodes
        if relays != self.lastRelays:
            # new relay, compute all node PDRs
            (nodePdrs, self.edgeNodes) = self._computeNodePDRs(tree, movingNode)
            self.lastNodePdrs = nodePdrs
        else:
            # same relays, just update PDR of moving node
            nodePdrs = self._updateNodePDR(
                lastNodePdrs=self.lastNodePdrs,
                movingNode=movingNode,
                edgeNodes=self.edgeNodes
            )

        # find success probability of packet reaching from sender to receiver
        successProbability = self._computeSuccessProbabilityCT(nodePdrs, movingNode)

        # store current relays and last tree
        self.lastRelays = relays

        self.lastTree = tree

        return successProbability

    def _updateTree(self, relays, movingNode, lastTree):

        if lastTree:
            # expand tree (take all the same branches except for the last node which is the previous moving node)
            branches_to_extend = [branch[:-1] for branch in lastTree]

        else:
            # start tree from root node
            branches_to_extend = [[self.rootNode]]

        # keep expanding each branch up to current moving node
        idx         = 0
        currentTree = []

        while branches_to_extend:
            branch          = branches_to_extend[idx]
            extension_nodes = list(set(relays+[movingNode]).difference(set(branch)))
            for node in extension_nodes:
                if node != movingNode:
                    if branch + [node] not in branches_to_extend:
                        branches_to_extend += [branch + [node]]

                else:
                    currentTree        += [branch + [node]]

                    branches_to_extend.remove(branch)

        return currentTree

    def _updateNodePDR(self, lastNodePdrs, movingNode, edgeNodes):
        # for every edge node, find pdr with moving node then multiply by edge connecting node pdr
        # remove the final entry from node PDRss and replace with new entry for this moving node
        # the finding success probability will be done in the same way

        nodePdrs                  = lastNodePdrs
        nodePdrs[movingNode]      = []

        for node in edgeNodes:
            if node[0] == movingNode and node[0] != self.rootNode:
                continue

            link_pdr = self._computePdrPisterHack(node[0],movingNode)

            nodePdrs[movingNode].append(link_pdr * node[1])

        return nodePdrs

    def _computeNodePDRs(self, tree, movingNode):

        # root is first link in first branch of tree
        root       = self.rootNode
        nodePdrs   = {root: [1]}

        # nodes at the ends of branches that connect to moving node
        # this is used to update node PDRs when only moving node changes
        edgeNodes  = []

        # compute PDR between all links in tree
        for branch in tree:

            # first link in branch is always starts at root (orchestrator)
            previousNode    = branch.pop(0)
            previousNodePdr = 1

            for node in branch:

                # find the PDR of the link between the two nodes
                linkPdr = self._computePdrPisterHack(
                    sender   = previousNode,    # node in link closer to root
                    receiver = node            # node in link closer to moving node
                )

                if node not in nodePdrs.keys():
                    nodePdrs[node] = []

                # node PDR = link PDR * PDR of previous node (node closer to root node)
                nodePdr         = round(linkPdr * previousNodePdr, 4)
                nodePdrs[node] += [nodePdr]

                # this is the edge node connected to the moving node
                if node == movingNode:
                    edgeNodes.append((previousNode, previousNodePdr))

                previousNode    = node
                previousNodePdr =  nodePdr

        return nodePdrs, edgeNodes

    def _computeSuccessProbabilityCT(self, nodePdrs, movingNode):

        nodes                = nodePdrs.keys()
        successProbabilities = {}

        for node in nodes:
            failure_probability           = round(np.prod([1 - node_pdr for node_pdr in list(set(nodePdrs[node]))]), 4)
            success_probability           = 1 - failure_probability
            successProbabilities[node]    = success_probability

        return successProbabilities[movingNode]  # final PDR of moving node through CT
    
