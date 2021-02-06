# built-in
import random
import time
import math
import threading
import copy
import time
import sys
# third-party
# local
import SimEngine
import Wireless
import Utils as u

class ExceptionOpenLoop(Exception):
    pass

class Navigation(object):

    def __init__(self,positions, floorplan):
        self.positions = positions
        self.floorplan = floorplan
        self.dotbotsview       = [ # the Orchestrator's internal view of the DotBots
            {
                'x':           x,
                'y':           y,
                'heading':     0,
                'last target': positions[0]
            } for (x,y) in self.positions
        ]
    #============================== private

    def _OneHopNeighborhood(self, x, y, shuffle=True):
        returnVal = []
        for (nx, ny) in [
            (x - 0.5, y - 0.5), (x , y-0.5), (x + 0.5, y - 0.5),
            (x - 0.5, y),                    (x + 0.5, y ),
            (x - 0.5, y + 0.5), (x , y+0.5), (x + 0.5, y + 0.5),
        ]:

            # only consider cells inside the realMap
            if (
                    (nx >= 0) and
                    (ny < self.floorplan.height) and
                    (ny >= 0) and
                    (nx < self.floorplan.width)
            ):
                returnVal += [(nx, ny)]

        if shuffle:
            random.shuffle(returnVal)
        return returnVal

    def _TwoHopNeighborhood(self, x, y):
        returnVal = []
        for (nx, ny) in [
            (x - 1, y - 1), (x - 0.5, y - 1), (x , y-1), (x + 0.5, y - 1), (x + 1 , y - 1),
            (x - 1, y - 0.5),                                              (x + 1, y - 0.5),
            (x - 1, y),                                                    (x + 1, y  ),
            (x + 0.5, y - 0.5),                                            (x + 1, y + 0.5),
            (x - 1, y + 1), (x - 0.5 , y + 1), (x, y+1), (x + 0.5, y + 1), (x + 1, y + 1)
        ]:

            # only consider cells inside the realMap
            if (
                    (nx >= 0) and
                    (ny < self.floorplan.height) and
                    (ny >= 0) and
                    (nx < self.floorplan.width)
            ):
                returnVal += [(nx, ny)]

        random.shuffle(returnVal)
        return returnVal

    def _dot_in_cell(self,dot, cellXmin, cellXmax, cellYmin, cellYmax ):
        (x_dot, y_dot) = dot
        if (x_dot >= cellXmin and x_dot <= cellXmax) and (y_dot >= cellYmin and y_dot <= cellYmax):
            return True
        else:
            return False

    def _oneStepCloser(self, rx, ry, tx, ty):
        (nx, ny) = (None, None)
        min_dist = None
        for (x, y) in self._OneHopNeighborhood(rx, ry, shuffle=True):
            known_map = self.mapBuilder.getMap()
            cell_has_obstacle = False
            for dot in known_map['dots']:
                if self._dot_in_cell(dot, x, y, x + self.floorplan.overlayWidth, y + self.floorplan.overlayHeight):
                    cell_has_obstacle = True
                    break

            #no walls and no robots
            if (
                    not cell_has_obstacle  and
                    (x, y) not in self.dotbotsview

            ):
                distToTarget = u.distance((x, y), (tx, ty))
                if (
                        min_dist == None or
                        distToTarget < min_dist
                ):
                    min_dist = distToTarget
                    (nx, ny) = (x, y)
        return (nx, ny)

    def _trajectory_on_cell(self, rx, ry, x2, y2, ax, ay, bx, by):
        # initial calculations (see algorithm)
        deltax = x2 - rx
        deltay = y2 - ry
        #                         left      right     bottom        top
        p = [-deltax, deltax, -deltay, deltay]
        q = [rx - ax, bx - rx, ry - ay, by - ry]

        # initialize u1 and u2
        u1 = 0
        u2 = 1

        # iterating over the 4 boundaries of the obstacle in order to find the t value for each one.
        # if p = 0 then the trajectory is parallel to that boundary
        # if p = 0 and q<0 then line completly outside boundaries

        # update u1 and u2
        for i in range(4):

            # abort if line outside of boundary

            if p[i] == 0:
                # line is parallel to boundary i

                if q[i] < 0:
                    return False
                pass  # nothing to do
            else:
                t = q[i] / p[i]
                if (p[i] < 0 and u1 < t):
                    u1 = t
                elif (p[i] > 0 and u2 > t):
                    u2 = t

        # if I get here, u1 and u2 should be set
        assert u1 is not None
        assert u2 is not None

        # decide what to return
        if (u1 > 0 and u1 < u2 and u2 < 1) or (0 < u1 < 1 and u1<u2) or (0 < u2 < 1 and u1<u2):
            return True
        else:
            return False

    def _calculate_heading(self, rx,ry,target_x,target_y):
        heading = (math.atan2(target_y-ry, target_x-rx) * 180.0 / math.pi + 180)-90
        if heading < 0:
            heading = (360-abs(heading))
        if heading > 360:
            heading  = (heading - 360) + 90
        return heading

class Navigation_Ballistic(Navigation):

    def __init__(self,positions, floorplan):
        Navigation.__init__(self,positions,floorplan)

    def get_new_heading(self, dotbotID, dotbot_position):

        dotbot = self.dotbotsview[dotbotID]

        (dotbot['x'], dotbot['y']) = dotbot_position
        new_heading = random.randint(0, 359)
        dotbot['heading'] = new_heading
        movementDur = None
        return (new_heading,movementDur)

class Navigation_Atlas(Navigation):
    def __init__(self, positions,floorplan):
        Navigation.__init__(self,positions,floorplan)
        self.exploredCells = []
        self.obstacle_cells = []
        self.open_cells = [positions[0]]

    def get_new_heading(self, dotbotID, dotbot_position):

        #find previous movement trajectory

        #find explored cells

        #check which explored cells are open and which have obstacles

        #check if previous target is in explored cells

        #find new target if previous target has been met

        #start checking cells around robot incrementaly
        #stop when unexplored cells are found

        #check easiest cells to reach (directly)
        #if not avaliable set movementDur of next heading

        # calculate heading to reach target (or first step towards target)

        new_heading = random.randint(0, 359)
        movementDur = 1

        return (new_heading,movementDur)

class MapBuilder(object):
    '''
    A background task which consolidates the map.
    It combines dots into lines
    It declares when the map is complete.
    '''

    PERIOD         = 1 # s, in simulated time
    MINFEATURESIZE = 0.9 # shortest wall, narrowest opening

    def __init__(self):

        # store params

        # local variables
        self.simEngine       = SimEngine.SimEngine()
        self.dataLock        = threading.RLock()
        self.simRun = 1
        self.discoMap = {
            'complete': False,    # is the map complete?
            'dots':     [],       # each bump becomes a dot
            'lines':    [],       # closeby dots are aggregated into a line
        }

        # schedule first housekeeping activity
        self.simEngine.schedule(self.simEngine.currentTime()+self.PERIOD,self._houseKeeping)
        self.exploredCells = []

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

        # stop the simulation run if mapping has completed
        if self.discoMap['complete']:
            self.simEngine.completeRun()

    def get_explored(self, exploredCells):
        self.exploredCells = exploredCells
    
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

            # map is not complete if mapping hasn't started
            if (not self.discoMap['dots']) and (not self.discoMap['lines']):
                returnVal = False
                break
            
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

class Orchestrator(Wireless.WirelessDevice):
    '''
    The central orchestrator of the expedition.
    '''
    
    COMM_DOWNSTREAM_PERIOD_S   = 1
    
    def __init__(self,numDotBots,initialPosition,navAlgorithm,floorplan):

        # store params
        self.numDotBots        = numDotBots
        self.initialPosition   = initialPosition
        self.floorplan         = floorplan # FIXME: remove

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
                'movementDur': None,
                'commandId':   0,
                'lastBumpTs':  None, # identify notifications which are retransmits # FIXME: replace by notifId
            } for (x,y) in [self.initialPosition]*self.numDotBots
        ]
        self.navAlgorithm      = getattr(sys.modules[__name__],'Navigation_{}'.format(navAlgorithm))([self.initialPosition]*self.numDotBots,self.floorplan)
        self.mapBuilder        = MapBuilder()
    
    #======================== public ==========================================

    #=== admin
    
    def startExploration(self):
        '''
        Simulation engine hands over control to orchestrator
        '''
        
        # choose an initial movement for the all DotBot # FIXME move to navigationAlgorithm
        for dotbot in self.dotbotsview:
            dotbot['heading'] = random.randint(0, 359)
            dotbot['speed']   = 1

        # arm first downstream communication
        self.simEngine.schedule(
            self.simEngine.currentTime()+self.COMM_DOWNSTREAM_PERIOD_S,
            self._downstreamTimeoutCb,
        )
        
    #=== communication

    def _downstreamTimeoutCb(self):
        
        # send downstream command
        self._sendDownstreamCommands()
        
        # arm next downstream communication
        self.simEngine.schedule(
            self.simEngine.currentTime()+self.COMM_DOWNSTREAM_PERIOD_S,
            self._downstreamTimeoutCb,
        )
    
    def _sendDownstreamCommands(self):
        '''
        Send the next heading and speed commands to the robots
        '''

        # format frame to transmit FIXME: ask Nav
        frameToTx = {
            'frameType': self.FRAMETYPE_COMMAND,
            'movements': [
                {
                    'heading':     dotbot['heading'],
                    'speed':       dotbot['speed'],
                    'movementDur': dotbot['movementDur']
                } for dotbot in self.dotbotsview
            ]
        }

        # hand over to wireless
        self.wireless.transmit(
            frame  = frameToTx,
            sender = self,
        )
    
    def receive(self,frame):
        '''
        A DotBot indicates its bump sensor was activated at a certain time
        '''
        assert frame['frameType']==self.FRAMETYPE_NOTIFICATION

        # shorthand
        dotbot = self.dotbotsview[frame['dotBotId']]

        # compute new position
        dotbot['x'] += (frame['tsMovementStop'] - frame['tsMovementStart']) * math.cos(math.radians(dotbot['heading'] - 90)) * dotbot['speed']
        dotbot['y'] += (frame['tsMovementStop'] - frame['tsMovementStart']) * math.sin(math.radians(dotbot['heading'] - 90)) * dotbot['speed']
        dotbot['x'] = round(dotbot['x'], 3)
        dotbot['y'] = round(dotbot['y'], 3)

        # notify the self.mapBuilder of the obstacle location
        # FIXME don't notify if not a bump
        self.mapBuilder.notifBump(dotbot['x'], dotbot['y'])

        # get new movement from navigation algorithm
        (new_heading,new_movementDur) = self.navAlgorithm.get_new_heading(frame['dotBotId'],(dotbot['x'], dotbot['y']))
        dotbot['heading']         = new_heading
        dotbot['speed']           = 1
        dotbot['movementDur']     = new_movementDur
    
    #=== UI
    
    def getView(self):
        '''
        Retrieves the approximate location of the DotBot for visualization.
        Attempts to compensate for current movement of robots.
        Might be wrong if DotBot has stopped.
        '''
        
        # do NOT write back any results to the DotBot's state as race condition possible
        # compute updated position

        dotbotlocations = [
            {
                'x': db['x'],
                'y': db['y'],
            } for db in self.dotbotsview
        ]
        
        return {
            'dotbots':  dotbotlocations,
            'discomap': self.mapBuilder.getMap(),
        }
    
    #======================== private =========================================
