# built-in
import random
# third-party
# local
import SimEngine
import Wireless

class Orchestrator(object):
    '''
    The central orchestrator of the expedition.
    '''
    
    def __init__(self,positions):
        
        # store params
        self.positions     = positions
        
        # local variables
        self.simEngine     = SimEngine.SimEngine()
        self.wireless      = Wireless.Wireless()
        self.dotbotsview   = [{ # the Orchestrator's internal view of the DotBot
            'x':           x,
            'y':           y,
            'posTs':       0,
            'heading':     0,
            'speed':       0,
        } for (x,y) in self.positions]
        self.bumpsview = [] # the Orchestrator's internal view of the location of the obstacles
    
    #======================== public ==========================================
    
    def startExploration(self):
        '''
        Simulation engine, start exploring
        '''
        for dotbot in self.dotbotsview:
            dotbot['heading'] = random.randint(230,300)
            dotbot['speed']   = 2*random.random()
        
        self._sendDownstreamCommands()
    
    def fromDotBot(self,msg):
        '''
        A DotBot indicates its bump sensor was activated at a certain time
        '''
        raise NotImplementedError()
    
    #======================== private =========================================
    
    def _sendDownstreamCommands(self):
        '''
        Send the next heading and speed commands to the robots
        '''
        
        # format msg
        msg = [
            {
                'heading': dotbot['heading'],
                'speed':   dotbot['speed'],
            } for dotbot in self.dotbotsview
        ]
        
        # hand over to wireless
        self.wireless.toDotBots(msg)
