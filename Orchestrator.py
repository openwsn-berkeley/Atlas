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
import Utils as u

class ExceptionOpenLoop(Exception):
    pass

class MapBuilder(object):
    '''
    A background task which consolidates the map.
    It combines dots into lines
    It declares when the map is complete.
    '''
    
    PERIOD         = 1 # s, in simulated time
    MINFEATURESIZE = 1 # shortest wall, narrowest opening
    
    def __init__(self):
        
        # store params
        
        # local variables
        self.simEngine       = SimEngine.SimEngine()
        self.dataLock        = threading.RLock()
        self.discoMap = {
            'complete': False,    # is the map complete?
            'dots':     [],       # each bump becomes a dot
            'lines':    [],       # closeby dots are aggregated into a line
        }
        
        # schedule first housekeeping activity
        self.simEngine.schedule(self.simEngine.currentTime()+self.PERIOD,self._houseKeeping)
    
    #======================== public ==========================================
    
    def notifBump(self,x,y):
        
        with self.dataLock:
            self.discoMap['dots'] += [(x,y)]
    
    def getMap(self):
        
        with self.dataLock:
            return copy.deepcopy(self.discoMap)
    
    #======================== private =========================================
    
    def _houseKeeping(self):
        
        with self.dataLock:
            # consolidate map
            self._consolidateMap()
            
            # decide whether map completed
            self.discoMap['complete'] = self._isMapComplete()
        
        # schedule next consolidation activity
        self.simEngine.schedule(self.simEngine.currentTime()+self.PERIOD,self._houseKeeping)
    
    def _consolidateMap(self):
            
        # result list of lines
        reslines                             = []
        
        # remove duplicate dots
        self.discoMap['dots']                = list(set(self.discoMap['dots']))
        
        # horizontal
        for direction in ['horizontal','vertical']:
            
            refs                             = []
            if direction=='horizontal':
                refs                        += [y   for (x,y)             in self.discoMap['dots']]               # all dots
                refs                        += [lay for (lax,lay,lbx,lby) in self.discoMap['lines'] if lay==lby ] # all horizontal lines
            else:
                refs                        += [x   for (x,y)             in self.discoMap['dots']]               # all dots
                refs                        += [lax for (lax,lay,lbx,lby) in self.discoMap['lines'] if lax==lbx ] # all vertical lines
            refs                             = set(refs)
            
            for ref in refs:
                
                # select all the dots which are aligned at this ref
                if direction=='horizontal':
                    thesedots                = [x for (x,y) in self.discoMap['dots'] if y==ref]
                else:
                    thesedots                = [y for (x,y) in self.discoMap['dots'] if x==ref]
                
                # select the lines we already know of at this ref
                if direction=='horizontal':
                    theselines               = [(lax,lay,lbx,lby) for (lax,lay,lbx,lby) in self.discoMap['lines'] if lay==ref and lby==ref]
                else:
                    theselines               = [(lax,lay,lbx,lby) for (lax,lay,lbx,lby) in self.discoMap['lines'] if lax==ref and lbx==ref]
                
                # remove dots which fall inside a line
                if direction=='horizontal':
                    thesedots                = [x for (x,y) in self._removeDotsOnLines([(x,ref) for x in thesedots] ,theselines)]
                else:
                    thesedots                = [y for (x,y) in self._removeDotsOnLines([(ref,y) for y in thesedots] ,theselines)]
                
                # add vertices of all lines to the dots
                for (lax,lay,lbx,lby) in theselines:
                    if direction=='horizontal':
                        thesedots           += [lax]
                        thesedots           += [lbx]
                    else:
                        thesedots           += [lay]
                        thesedots           += [lby]
                
                # remove duplicates (in case dot falls on vertice of existing line)
                thesedots                    = list(set(thesedots))
                
                # sort dots by increasing value
                thesedots                    = sorted(thesedots)
                
                # create line between close dots
                for (idx,v) in enumerate(thesedots):
                    if idx==len(thesedots)-1:
                        continue
                    vnext                    = thesedots[idx+1]
                    if vnext-v<=self.MINFEATURESIZE:
                        if direction=='horizontal':
                            theselines      += [(v,ref,vnext,ref)]
                        else:
                            theselines      += [(ref,v,ref,vnext)]
                
                # remove line duplicates (caused by short lines which turn into close points)
                theselines                   = list(set(theselines))
                
                # join the lines that touch
                if direction=='horizontal':
                    theselines = sorted(theselines,key = lambda l: l[0])
                else:
                    theselines = sorted(theselines,key = lambda l: l[1])
                idx = 0
                while idx<len(theselines)-1:
                    (lax,lay,lbx,lby)        = theselines[idx]
                    (nax,nay,nbx,nby)        = theselines[idx+1]
                    if direction=='horizontal':
                        condition            = (lbx==nax)
                    else:
                        condition            = (lby==nay)
                    if condition:
                        theselines[idx]      = (lax,lay,nbx,nby)
                        theselines.pop(idx+1)
                    else:
                        idx                 += 1
                
                # store
                reslines                    += theselines
        
        # store
        self.discoMap['lines']               = reslines
        
        # remove duplicate dots
        self.discoMap['dots']                = list(set(self.discoMap['dots']))
        
        # remove dots which fall inside a line
        self.discoMap['dots']                = self._removeDotsOnLines(self.discoMap['dots'],self.discoMap['lines'])
    
    def _removeDotsOnLines(self,dots,lines):
        idx = 0
        while idx<len(dots):
            (dx,dy)                              = dots[idx]
            removed                              = False
            for (lax,lay,lbx,lby) in lines:
                if   lay==lby and lay==dy:
                    # horizontal line, co-linear to point
                    
                    condition                    = lax<=dx and dx<=lbx
                elif lax==lbx and lax==dx:
                    # vertical line,   co-linear to point
                    
                    condition                    = lay<=dy and dy<=lby
                else:
                    # not co-linear to point
                    condition                    = False
                if condition:
                    dots.pop(idx)
                    removed                      = True
                    break
            if removed==False:
                idx                             += 1
        return dots
    
    def _isMapComplete(self):
        
        while True: # "loop" only once
            
            # map is never complete if there are dots remaining
            if self.discoMap['dots']:
                returnVal = False
                break
            
            # keep looping until no more todo lines
            alllines = copy.deepcopy(self.discoMap['lines'])
            try:
                while alllines:
                    loop      = self._walkloop(alllines,alllines[0])
                    for line in loop:
                        alllines.remove(line)
            except ExceptionOpenLoop:
                returnVal = False
                break
            
            # if I get here, map is complete
            returnVal = True
            break
        
        return returnVal
    
    def _walkloop(self,alllines,startline):
        
        loop  = []
        loop += [startline]
        while True:
            # add close line to loop
            foundCloseLine = False
            for line in alllines:
                if (self._areLinesClose(loop[-1],line)) and (line not in loop):
                    foundCloseLine = True
                    loop          += [line]
                    break
            
            # abort if no next line to hop to
            if foundCloseLine==False:
                
                raise ExceptionOpenLoop()
            # success! last line in loop is close to first line
            if len(loop)>2 and self._areLinesClose(loop[-1],loop[0]):
                
                return loop
    
    def _areLinesClose(self,line1,line2):
        
        (l1ax,l1ay,l1bx,l1by) = line1
        (l2ax,l2ay,l2bx,l2by) = line2
        
        returnVal = False
        
        while True: # "loop" only once
            if  u.distance((l1ax,l1ay),(l2ax,l2ay))<=self.MINFEATURESIZE:
                returnVal = True
                break
            if  u.distance((l1ax,l1ay),(l2bx,l2by))<=self.MINFEATURESIZE:
                returnVal = True
                break
            if  u.distance((l1bx,l1by),(l2ax,l2ay))<=self.MINFEATURESIZE:
                returnVal = True
                break
            if  u.distance((l1bx,l1by),(l2bx,l2by))<=self.MINFEATURESIZE:
                returnVal = True
                break
            break
        
        return returnVal

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
        self.mapBuilder        = MapBuilder()
    
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
        
        # notify the self.mapBuilder the obstacle location
        self.mapBuilder.notifBump(dotbot['x'],dotbot['y'])
        
        # adjust the heading of the DotBot which bumped (avoid immediately bumping into the same wall)
        dotbot['heading']        = random.randint(  0,359)
        
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
        
        return {
            'dotbots': [
                {
                    'x': db['x']+(now-db['posTs'])*math.cos(math.radians(db['heading']-90))*db['speed'],
                    'y': db['y']+(now-db['posTs'])*math.sin(math.radians(db['heading']-90))*db['speed'],
                } for db in self.dotbotsview
            ],
            'discomap': self.mapBuilder.getMap(),
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
