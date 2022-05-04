# built-in
import random
# built-in
# local

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
    DFLT_PDR  = 1.0

    # singleton pattern
    _instance = None
    _init     = False

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
        self.devices = []
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
            if random.uniform(0,1) < self.DFLT_PDR:
                receiver.receive(frame)

    # ======================== private =========================================
