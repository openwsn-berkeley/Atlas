# built-in
import random
import math
import threading
import copy
import time
# third-party
# local
import SimEngine
import Wireless

class MapBuilder(threading.Thread):
    '''
    A background task which consolidates the map.
    It combines dots into lines
    It declares when the map is complete.
    '''
    
    PERIOD         = 1 # FIXME: in simulated time?
    MINFEATURESIZE = 1 # shortest wall, narrowest opening
    
    def __init__(self,discoMap,dataLock):
        
        # store params
        self.discoMap        = discoMap
        self.dataLock        = dataLock
        
        # start thread
        threading.Thread.__init__(self)
        self.name            = 'MapBuilder'
        self.daemon          = True
        self.start()
    
    def run(self):
        while True:
            
            # wait a bit between consolidation actions
            time.sleep(self.PERIOD)
            
            # consolidate
            with self.dataLock:
                self._consolidateMap(self.discoMap)
    
    def _consolidateMap(self,discoMap):
        '''
        self.discoMap['lines'] += [
            (
                random.randint(0,18),
                random.randint(0,6),
                random.randint(0,18),
                random.randint(0,6),
            )
        ]
        '''
        pass

class Orchestrator(object):
    '''
    The central orchestrator of the expedition.
    '''
    
    def __init__(self,positions,floorplan):
        
        # store params
        self.positions         = positions
        self.floorplan         = floorplan
        
        # local variables
        self.simEngine         = SimEngine.SimEngine()
        self.wireless          = Wireless.Wireless()
        self.dotbotsview       = [ # the Orchestrator's internal view of the DotBots
            {
                'x':           x,
                'y':           y,
                'posTs':       0,
                'heading':     0,
                'speed':       0,
                'commandId':   0,
            } for (x,y) in self.positions
        ]
        # the map the orchestrator is building
        self.mapLock           = threading.RLock()
        self.discoMap = {
            'complete': False,    # is the map complete?
            'dots':     [],       # each bump becomes a dot
            'lines':    [],       # closeby dots are aggregated into a line
        }
        self.mapBuilder        = MapBuilder(self.discoMap,self.mapLock)
    
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
        dotbot['x']             += (msg['bumpTs']-dotbot['posTs'])*math.cos(math.radians(dotbot['heading']-90))*dotbot['speed']
        dotbot['y']             += (msg['bumpTs']-dotbot['posTs'])*math.sin(math.radians(dotbot['heading']-90))*dotbot['speed']
        dotbot['posTs']          = msg['bumpTs']
        
        # record the obstacle location
        with self.mapLock:
            self.discoMap['dots'] += [(dotbot['x'],dotbot['y'])]
        
        # round
        dotbot['x']              = round(dotbot['x'],3)
        dotbot['y']              = round(dotbot['y'],3)
        
        # adjust the heading of the DotBot which bumped (avoid immediately bumping into the same wall)
        against_N_wall           = math.isclose(dotbot['y'],                    0,abs_tol=10**-3)
        against_E_wall           = math.isclose(dotbot['x'], self.floorplan.width,abs_tol=10**-3)
        against_S_wall           = math.isclose(dotbot['y'],self.floorplan.height,abs_tol=10**-3)
        against_W_wall           = math.isclose(dotbot['x'],                    0,abs_tol=10**-3)
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
        
        # do NOT write back any results to the DotBot's state as race condition possible
        
        # compute updated position
        now         = self.simEngine.currentTime() # shorthand
        
        with self.mapLock:
            discoMapCopy = copy.deepcopy(self.discoMap)
        return {
            'dotbots': [
                {
                    'x': db['x']+(now-db['posTs'])*math.cos(math.radians(db['heading']-90))*db['speed'],
                    'y': db['y']+(now-db['posTs'])*math.sin(math.radians(db['heading']-90))*db['speed'],
                } for db in self.dotbotsview
            ],
            'discomap': discoMapCopy,
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
