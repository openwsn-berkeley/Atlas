# built-in
import random
import math
# third-party
# local
import SimEngine
import Wireless

class Orchestrator(object):
    '''
    The central orchestrator of the expedition.
    '''
    
    def __init__(self,positions,floorplan):
        
        # store params
        self.positions     = positions
        self.floorplan     = floorplan
        
        # local variables
        self.simEngine     = SimEngine.SimEngine()
        self.wireless      = Wireless.Wireless()
        self.dotbotsview   = [ # the Orchestrator's internal view of the DotBots
            {
                'x':           x,
                'y':           y,
                'posTs':       0,
                'heading':     0,
                'speed':       0,
            } for (x,y) in self.positions
        ]
        self.bumpsview = [] # the Orchestrator's internal view of the location of the obstacles
    
    #======================== public ==========================================
    
    def startExploration(self):
        '''
        Simulation engine, start exploring
        '''
        for dotbot in self.dotbotsview:
            dotbot['heading'] = random.randint(0,359)
            dotbot['speed']   = 1
        
        self._sendDownstreamCommands()
    
    def fromDotBot(self,msg):
        '''
        A DotBot indicates its bump sensor was activated at a certain time
        '''
        
        dotbot = self.dotbotsview[msg['dotBotId']] # shorthand
        
        # compute new theoretical position
        dotbot['x']         += (msg['bumpTs']-dotbot['posTs'])*math.cos(math.radians(dotbot['heading']-90))*dotbot['speed']
        dotbot['y']         += (msg['bumpTs']-dotbot['posTs'])*math.sin(math.radians(dotbot['heading']-90))*dotbot['speed']
        dotbot['posTs']      = msg['bumpTs']
        
        # adjust the heading of the DotBot which bumped (avoid immediately bumping into same wall)
        if   math.isclose(dotbot['x'],                    0,abs_tol=10**-3):   # against West wall
            dotbot['heading']    = random.randint(0,180)
        elif math.isclose(dotbot['x'], self.floorplan.width,abs_tol=10**-3):   # against East wall
            dotbot['heading']    = random.randint(180,359)
        elif math.isclose(dotbot['y'],                    0,abs_tol=10**-3):   # against North wall
            dotbot['heading']    = random.randint(90,270)
        elif math.isclose(dotbot['y'],self.floorplan.height,abs_tol=10**-3):   # against South wall
            dotbot['heading']    = random.randint(270,360+90)
            dotbot['heading']    = dotbot['heading']%360
        else:                                    # in the middle of field
            dotbot['heading']    = random.randint(0,359)
        
        # send commands to the robots
        self._sendDownstreamCommands()
    
    def getView(self):
    
        # update position
        now         = self.simEngine.currentTime() # shorthand
        for dotbot in self.dotbotsview:
            dotbot['x']     += (now-dotbot['posTs'])*math.cos(math.radians(dotbot['heading']-90))*dotbot['speed']
            dotbot['y']     += (now-dotbot['posTs'])*math.sin(math.radians(dotbot['heading']-90))*dotbot['speed']
            dotbot['posTs']  = now
    
        return [
            {
                'x': e['x'],
                'y': e['y'],
            } for e in self.dotbotsview
        ]
    
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
