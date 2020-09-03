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

class MapBuilder(object):
    '''
    A background task which consolidates the map.
    It combines dots into lines
    It declares when the map is complete.
    '''
    
    PERIOD         = 1 # s, in simulated time
    MINFEATURESIZE = 1  # shortest wall, narrowest opening
    
    def __init__(self,discoMap,dataLock):
        
        # store params
        self.discoMap        = discoMap
        self.dataLock        = dataLock
        
        # local variables
        self.simEngine         = SimEngine.SimEngine()
        
        # schedule first consolidation activity
        self.simEngine.schedule(self.simEngine.currentTime()+self.PERIOD,self._consolidateMap)
    
    def _consolidateMap(self):
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
        
        with self.dataLock:
            
            # results lists of (lone) dots and lines
            reslonedots                     = []
            reslines                        = []
            
            # artificially add dots at the vertices of all lines
            # TODO
            
            # remove duplicate dots
            self.discoMap['dots']           = list(set(self.discoMap['dots']))
            
            # horizontal
            print('\n\n========================================================')
            print (self.discoMap['dots'])
            for direction in ['horizontal','vertical']:
                
                print('======= {0}'.format(direction))
                
                if direction=='horizontal':
                    refs                         = set([y for (x,y) in self.discoMap['dots']])
                else:
                    refs                         = set([y for (x,y) in self.discoMap['dots']])
                
                for ref in refs:
                    print('ref:  {0}'.format(ref))
                    
                    # select all the dots which are aligned at this ref
                    if direction=='horizontal':
                        thesedots                = [x for (x,y) in self.discoMap['dots'] if y==ref]
                    else:
                        thesedots                = [y for (x,y) in self.discoMap['dots'] if x==ref]
                    print('len(thesedots):      {0}'.format(len(thesedots)))
                    
                    # there can be no line if there is only one: it's a lone dot
                    if len(thesedots)==1:
                        reslonedots             += [(thesedots[0],ref)]
                        continue
                    
                    # select the lines we already know of at this ref
                    if direction=='horizontal':
                        theselines               = [(lax,lay,lbx,lby) for (lax,lay,lbx,lby) in self.discoMap['lines'] if lay==ref and lby==ref]
                    else:
                        theselines               = [(lax,lay,lbx,lby) for (lax,lay,lbx,lby) in self.discoMap['lines'] if lax==ref and lbx==ref]
                    print('len(theselines):     {0}'.format(len(theselines)))
                    
                    # sort dots by increasing value
                    thesedots                   = sorted(thesedots)
                    print('len(thesedots):      {0}'.format(len(thesedots)))
                    
                    # remove dots which fall inside a line
                    idx = 0
                    while idx<len(thesedots):
                        v                       = thesedots[idx]
                        removeOne               = False
                        for (lax,lay,lbx,lby) in theselines:
                            if direction=='horizontal':
                                condition       = lax<=v and v<=lbx
                            else:
                                condition       = lay<=v and v<=lby
                            if condition:
                                thesedots.pop(idx)
                                removeOne       = True
                                break
                        if removeOne==False:
                            idx                += 1
                    print('len(thesedots):      {0}'.format(len(thesedots)))
                    
                    # add vertices of all lines to the dots (and sort)
                    for (lax,lay,lbx,lby) in theselines:
                        if direction=='horizontal':
                            thesedots          += [lax]
                            thesedots          += [lbx]
                        else:
                            thesedots          += [lay]
                            thesedots          += [lby]
                    thesedots                   = sorted(thesedots)
                    print('len(thesedots):      {0}'.format(len(thesedots)))
                    
                    # create line between close dots; remainder dots are lonedots
                    for (idx,v) in enumerate(thesedots):
                        if idx==len(thesedots)-1:
                            if lastdotlone:
                                if direction=='horizontal':
                                    reslonedots+= [(v,ref)]
                                else:
                                    reslonedots+= [(ref,v)]
                            continue
                        vnext                   = thesedots[idx+1]
                        if vnext-v<=self.MINFEATURESIZE:
                            if direction=='horizontal':
                                theselines     += [(v,ref,vnext,ref)]
                            else:
                                theselines     += [(ref,v,ref,vnext)]
                            lastdotlone         = False
                        else:
                            if direction=='horizontal':
                                reslonedots    += [(v,ref)]
                            else:
                                reslonedots    += [(ref,v)]
                            lastdotlone         = True
                    print('len(theselines):     {0}'.format(len(theselines)))
                    print('len(reslonedots):    {0}'.format(len(reslonedots)))
                    
                    # join lines which touch
                    theselines = sorted(theselines,key = lambda l: l[0])
                    idx = 0
                    while idx<len(theselines)-1:
                        (lax,lay,lbx,lby)       = theselines[idx]
                        (nax,nay,nbx,nby)       = theselines[idx+1]
                        if direction=='horizontal':
                            condition           = (lbx==nax)
                        else:
                            condition           = (lby==nay)
                        if condition:
                            theselines[idx]     = (lax,lay,nbx,nby)
                            theselines.pop(idx+1)
                        else:
                            idx                += 1
                    print('len(theselines):     {0}'.format(len(theselines)))
                    
                    # store lines
                    reslines                   += theselines
            
            # remove lone dots that are vertices of lines
            idx = 0
            while idx<len(reslonedots):
                deleted = False
                for (lax,lay,lbx,lby) in reslines:
                    if reslonedots[idx]==(lax,lay) or reslonedots[idx]==(lbx,lby):
                        reslonedots.pop(idx)
                        deleted             = True
                        break
                if deleted == False:
                    idx                    += 1
            
            # update main structure
            self.discoMap['dots']           = reslonedots
            self.discoMap['lines']          = reslines
            print("len(self.discoMap['dots']):     {0}".format(len(self.discoMap['dots'])))
            print("len(self.discoMap['lines']):    {0}".format(len(self.discoMap['lines'])))
            
        
        # schedule next consolidation activity
        self.simEngine.schedule(self.simEngine.currentTime()+self.PERIOD,self._consolidateMap)

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
        
        # round
        dotbot['x']              = round(dotbot['x'],3)
        dotbot['y']              = round(dotbot['y'],3)
        
        # record the obstacle location
        with self.mapLock:
            self.discoMap['dots'] += [(dotbot['x'],dotbot['y'])]
        
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
