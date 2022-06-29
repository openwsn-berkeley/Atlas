# built-in
import random
import math
# built-in
# third-party
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
        self.devices         = []
        self.lastPositions   = {}
        self.lastStabilities = {}

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
        self._init     = False

    def transmit(self, sender, frame):
        relays = [device for device in self.devices if device.isRelay]

        for receiver in self.devices:

            if receiver == sender:
                continue  # transmitter doesn't receive

            assert sender != receiver

            # get pdr between sender and receiver
            pdr            = self._getPDR(sender, relays, receiver)

            # only log pdr when pdr is critically low
            if pdr < 0.1 :
                log.debug(f'PDR between {(sender.x, sender.y)} and {(receiver.x, receiver.y)} is {pdr}')

            if random.uniform(0, 1) < pdr:
                receiver.receive(frame)

    # ======================== private =========================================

    def _getPDR(self, sender, relays, receiver):

        # find probability of failure between sender and receiver with no relays
        failProbability = (1 - self._getStability(sender, receiver))

        for relay in relays:

            if relay == receiver:
                continue

            # find probability of failure for every path of (sender -> relay -> receiver)
            stabilitySenderRelay   = self._getStability(sender, relay)
            stabilityRelayReceiver = self._getStability(relay,  receiver)
            failProbability        = failProbability * (1-(stabilitySenderRelay * stabilityRelayReceiver))

        return 1 - failProbability     # probability of success

    def _getStability(self, sender, receiver):
        '''
        Pister Hack model for PDR calculation based on distance/ signal attenuation
        '''

        # get current positions of sender and reciever
        (receiverX, receiverY) = receiver.computeCurrentPosition()
        (senderX, senderY)     = sender.computeCurrentPosition()

        # find if (nodeA, nodeB) or (nodeB, nodeA) are in the lastStabilities keys.
        # set that as the key to use to find the value of the pdr
        linkInLastStabilities = {
            (sender.dotBotId, receiver.dotBotId),
            (receiver.dotBotId, sender.dotBotId)
        }.intersection(self.lastStabilities.keys())

        if (
            # both sender and receiver are in are in last positions and the link between
            sender.dotBotId in self.lastPositions.keys() and
            receiver.dotBotId in self.lastPositions.keys() and
            # sender and receiver haven't moved since last time their link stability was computed
            (senderX, senderY) == self.lastPositions[sender.dotBotId] and
            (receiverX, receiverY) == self.lastPositions[receiver.dotBotId] and
            # the link between sender and receiver is in last stabilities
            linkInLastStabilities
        ):

            # link stability between sender and receiver is the same as last time
            pdr = self.lastStabilities[list(linkInLastStabilities)[0]]

        else:

            distance    = u.distance((sender.x, sender.y), (receiver.x, receiver.y))
            shift_value = random.uniform(0, self.PISTER_HACK_LOWER_SHIFT)
            rssi        = self._friisModel(distance) - shift_value
            pdr         = self._rssi_to_pdr(rssi)

            self.lastPositions[sender.dotBotId]   = (sender.x,   sender.y)
            self.lastPositions[receiver.dotBotId] = (receiver.x, receiver.y)
            self.lastStabilities[(sender.dotBotId, receiver.dotBotId)] = pdr

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

