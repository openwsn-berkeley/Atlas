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
                'commandId':   0,
            } for (x,y) in self.positions
        ]
        self.discoveredobstacles = [] # the Orchestrator's internal view of the location of the obstacles
    
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
        
        # shorthand
        dotbot = self.dotbotsview[msg['dotBotId']]
        
        # compute new theoretical position
        dotbot['x']         += (msg['bumpTs']-dotbot['posTs'])*math.cos(math.radians(dotbot['heading']-90))*dotbot['speed']
        dotbot['y']         += (msg['bumpTs']-dotbot['posTs'])*math.sin(math.radians(dotbot['heading']-90))*dotbot['speed']
        dotbot['posTs']      = msg['bumpTs']
        
        # record the obstacle location
        #poipoipoiself.discoveredobstacles += [(dotbot['x'],dotbot['y'])]
        
        # round
        dotbot['x']          = round(dotbot['x'],3)
        dotbot['y']          = round(dotbot['y'],3)
        
        # adjust the heading of the DotBot which bumped (avoid immediately bumping into the same wall)
        against_N_wall       = math.isclose(dotbot['y'],                    0,abs_tol=10**-3)
        against_E_wall       = math.isclose(dotbot['x'], self.floorplan.width,abs_tol=10**-3)
        against_S_wall       = math.isclose(dotbot['y'],self.floorplan.height,abs_tol=10**-3)
        against_W_wall       = math.isclose(dotbot['x'],                    0,abs_tol=10**-3)
        if   against_N_wall and against_W_wall:            # NW corner
            dotbot['heading']    = random.randint( 90,180)
        elif against_N_wall and against_E_wall:            # NE corner
            dotbot['heading']    = random.randint(180,270)
        elif against_S_wall and against_E_wall:            # SE corner
            dotbot['heading']    = random.randint(270,359)
        elif against_S_wall and against_W_wall:            # SW corner
            dotbot['heading']    = random.randint(  0, 90)
        elif against_N_wall:                               # N  wall
            dotbot['heading']    = random.randint( 90,270)
        elif against_E_wall:                               # E  wall
            dotbot['heading']    = random.randint(180,359)
        elif against_S_wall:                               # S  wall
            dotbot['heading']    = random.randint(270,360+90)
            dotbot['heading']    = dotbot['heading']%360
        elif against_W_wall:                               # W  wall
            dotbot['heading']    = random.randint(  0,180)
        else:                                              # in the middle of field
            dotbot['heading']    = random.randint(  0,359)
        
        # set the DotBot's speed
        dotbot['speed']          = 1
        
        # bump command Id so DotBot knows this is not a duplicate command
        dotbot['commandId']     += 1
        
        # send commands to the robots
        self._sendDownstreamCommands()
    
    def getView(self):
    
        # update position
        now         = self.simEngine.currentTime() # shorthand
        for dotbot in self.dotbotsview:
            dotbot['x']     += (now-dotbot['posTs'])*math.cos(math.radians(dotbot['heading']-90))*dotbot['speed']
            dotbot['y']     += (now-dotbot['posTs'])*math.sin(math.radians(dotbot['heading']-90))*dotbot['speed']
            dotbot['posTs']  = now
    
        return {
            'dotbots': [
                {
                    'x': e['x'],
                    'y': e['y'],
                } for e in self.dotbotsview
            ],
            'discoveredobstacles': self.discoveredobstacles,
        }
    
    #======================== private =========================================
    
    def _sendDownstreamCommands(self):
        '''
        Send the next heading and speed commands to the robots
        '''
        
        # format msg
        msg = [
            {
                'commandId': dotbot['commandId'],
                'heading':   dotbot['heading'],
                'speed':     dotbot['speed'],
            } for dotbot in self.dotbotsview
        ]
        
        # hand over to wireless
        self.wireless.toDotBots(msg)
