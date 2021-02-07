# built-in
import random
# third-party
# local
import Utils as u

class WirelessDevice(object):
    '''
    Abstract class for any device communicating over the wireless medium.
    '''
    
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
    
    PDR = 1.0 # FIXME: PisterHack
    
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

        # local variables

    # ======================== public ==========================================
    
    def indicateDevices(self,devices):
        self.devices         =  devices
    
    def destroy(self): 
        self._instance       = None
        self._init           = False

    def transmit(self, frame, sender):
        assert self.devices # make sure there are devices
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
        return self.PDR # FIXME: PisterHack
    
    def _get_pisterHack_PDR(self,sender,receiver):
        '''
        Pister Hack model for PDR calculation based on distance/ signal attenuation
        '''
        if self.packetCounter == 0:
            dotbotX = self.orchX
            dotbotY = self.orchY
        else:
            (dotbotX,dotbotY) = dotbot.computeCurrentPosition()

        distance = int(u.distance((dotbotX,dotbotY),(self.orchX,self.orchY)))
        distanceToPDR = {
                     '23': 0.0001, '22': 0.0001, '21': 0.0001, '20': 0.0001, '19': 0.0001,
                     '18': 0.0001, '17': 0.1494, '16': 0.2340, '15': 0.4071, '14': 0.6359,
                     '13': 0.6866, '12': 0.7476, '11':0.8603, '10': 0.8702, '9':   0.9324,
                      '8': 0.9427 , '7': 0.9562, '6': 0.9611, '5': 0.9739, '4': 0.9745,
                      '3': 0.9844, '2': 0.9854, '1': 0.9903, '0': 1.0000,
                         }
        PDR = distanceToPDR[str(distance)]

        return PDR
