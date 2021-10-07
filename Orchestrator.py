# built-in
import random
import threading
import copy
import sys
import math
import logging

from typing import Union, Optional, List

# third-party
# local
import SimEngine
import Wireless
import Utils as u

from atlas.algorithms.planning import Map, AStar

class ExceptionOpenLoop(Exception):
    pass

class MapBuilder(object):
    '''
    A background task which consolidates the map.
    It combines dots into lines
    It declares when the map is complete.
    '''

    HOUSEKEEPING_PERIOD_S    = 60    # in simulated time
    MINFEATURESIZE_M         = 1.00 # shortest wall, narrowest opening

    def __init__(self):

        # store params

        # local variables
        self.simEngine       = SimEngine.SimEngine()
        self.dataLock        = threading.RLock()
        self.discoMap        = {
            'complete': False,    # is the map complete?
            'dots':     [],       # each bump becomes a dot
            'lines':    [],       # closeby dots are aggregated into a line
        }

        # schedule first housekeeping activity
        self.simEngine.schedule(self.simEngine.currentTime()+self.HOUSEKEEPING_PERIOD_S,self._houseKeeping)
        self.exploredCells = []
        self.numRelayBots  = 0
        self.numDotBots    = 0

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
        self.simEngine.schedule(self.simEngine.currentTime()+self.HOUSEKEEPING_PERIOD_S,self._houseKeeping)

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
                allDots = self.discoMap['dots']
                allDots += [(lax,lay) for (lax,lay,lbx,lby) in self.discoMap['lines']]
                allDots += [(lbx, lby) for (lax, lay, lbx, lby) in self.discoMap['lines']]

                if direction=='horizontal':
                    thesedots                = [x for (x,y) in allDots if y==ref]
                else:
                    thesedots                = [y for (x,y) in allDots if x==ref]

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

                    if vnext-v<self.MINFEATURESIZE_M:

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

        #print(self.numDotBots, self.numRelayBots)
        if (self.numRelayBots >= self.numDotBots) and self.numRelayBots > 0:
            return True

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
            if  u.distance((l1ax,l1ay),(l2ax,l2ay))<self.MINFEATURESIZE_M/2:
                returnVal = True
                break
            if  u.distance((l1ax,l1ay),(l2bx,l2by))<self.MINFEATURESIZE_M/2:
                returnVal = True
                break
            if  u.distance((l1bx,l1by),(l2ax,l2ay))<self.MINFEATURESIZE_M/2:
                returnVal = True
                break
            if  u.distance((l1bx,l1by),(l2bx,l2by))<self.MINFEATURESIZE_M/2:
                returnVal = True
                break
            break

        return returnVal

# TODO: make this an abstract base class with ABC
class Navigation(object):

    def __init__(self, numDotBots, initialPosition: Union[tuple, List[tuple]], *args, **kwargs):

        # store params
        self.numDotBots      = numDotBots
        self.initialPosition = initialPosition
        
        # local variables
        self.dotbotsview     = [
            {
                'ID':                       id,
                # evaluated position of the DotBot when it last stopped
                'x':                        x,
                'y':                        y,
                # current movement
                'heading':                  0,
                'speed':                    0,
                'seqNumMovement':           0,
                'seqNumNotification':       None,
                # for Atlas
                'target':                   None,
                'timer':                    None,
                'previousPath':             [],
                'heartbeat':                1,
                'pdrHistory':               [],
                'pdrStatus':                None,


            } for [id,(x,y)] in enumerate([self.initialPosition]*self.numDotBots) # TODO: handle initial position List
        ]
        self.mapBuilder       = MapBuilder()
        self.movingDuration   = 0
        self.heatmap          = [(self.initialPosition, 0)] # TODO: handle initial position List
        self.profile          = []
        self.relayProfile     = []
        self.pdrProfile       = []
        self.timeLine         = []
        self.heartbeat        = 1
        self.pdrStatus        = None


    
    #======================== public ==========================================
    
    def receiveNotification(self,frame):
        '''
        We just received a notification for a DotBot.
        '''
        
        # shorthand
        dotbot      = self.dotbotsview[frame['dotBotId']]
        self.bump   = frame['bump']

        if frame['heartbeat']:
            self.heartbeat = frame['heartbeat']
            self.pdrStatus = frame['pdrStatus']
            return
        # filter out duplicates
        if frame['seqNumNotification'] == dotbot['seqNumNotification']:
            return
        dotbot['seqNumNotification'] = frame['seqNumNotification']


        # update DotBot's position
        (newX,newY)  = u.computeCurrentPosition(
            currentX = dotbot['x'],
            currentY = dotbot['y'],
            heading  = dotbot['heading'],
            speed    = dotbot['speed'],
            duration = frame['tsMovementStop'] - frame['tsMovementStart'],
        )

        self.movingDuration = frame['tsMovementStop'] - frame['tsMovementStart']

        self._notifyDotBotMoved(dotbot['x'],dotbot['y'],newX,newY)
        (dotbot['x'],dotbot['y']) = (newX,newY)

        if self.bump == True:
            # notify the mapBuilder of the obstacle location
            self.mapBuilder.notifBump(dotbot['x'], dotbot['y'])

        # compute new DotBot movement
        self._updateMovement(frame['dotBotId'])

    def getEvaluatedPositions(self):
        '''
        Retrieve the evaluated positions of each DotBot.
        '''
        returnVal = [
            {
                'x':         dotbot['x'],
                'y':         dotbot['y'],
            } for dotbot in self.dotbotsview
        ]
        return returnVal

    def getMovements(self):
        '''
        Retrieve the movement of all DotBots.
        '''
        returnVal = [
            {
                'ID':                        dotbot['ID'],
                'heading':                   dotbot['heading'],
                'speed':                     dotbot['speed'],
                'seqNumMovement':            dotbot['seqNumMovement'],
                'timer':                     dotbot['timer'],


            } for dotbot in self.dotbotsview
        ]
        return returnVal

    def getExploredCells(self):
        raise SystemError('abstract method')

    def getHeatmap(self):
        raise SystemError('abstract method')

    def getProfile(self):
        raise SystemError('abstract method')

    def getRelayProfile(self):
        raise SystemError('abstract method')

    def getPDRprofile(self):
        raise SystemError('abstract method')

    #======================== private =========================================

    def _notifyDotBotMoved(self,oldX,oldY,newX,newY):
        raise SystemError('abstract method')

    def _updateMovement(self,dotBotId):
        raise SystemError('abstract method')

class NavigationBallistic(Navigation):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # initial movements are random
        for (dotBotId,_) in enumerate(self.dotbotsview):
            self._updateMovement(dotBotId)

    #======================== public ==========================================

    def getExploredCells(self):
        return {} # Ballistic doesn't keep track of explored areas

    #======================== private =========================================

    def _notifyDotBotMoved(self,oldX,oldY,newX,newY):
        pass # Ballistic doesn't act on DotBot movement

    def _updateMovement(self, dotBotId):
        '''
        \post modifies the movement directly in dotbotsview
        '''

        # shorthand
        dotbot = self.dotbotsview[dotBotId]

        # pick new movement
        dotbot['heading']         = random.randint(0, 359)
        dotbot['speed']           = 1
        dotbot['seqNumMovement'] += 1

class NavigationAtlas(Navigation):

    def __init__(self, *args, relayAlg="recovery", **kwargs):

        # initialize parent
        super().__init__(*args, **kwargs)

        self.map = Map(offset=self.initialPosition, scale=MapBuilder.MINFEATURESIZE_M / 2, cell_class=AStar.Cell)
        self.path_planner = AStar(self.map)

        # (additional) local variables
        self.simEngine = SimEngine.SimEngine()
        # shorthands for initial x,y position
        self.ix                = self.initialPosition[0]
        self.iy                = self.initialPosition[1]
        # a "half-cell" is identified by its center, and has side MINFEATURESIZE_M/2
        self.hCellsUnreachable = []
        # the hCell the DotBot start is in, by definition, open
        self.relayBots         = [] # have not been given destinations
        self.positionedRelays  = [] # have been given destinations, but have not reached them
        self.relayPositions    = [] # desired positions to fill?
        self.readyRelays       = [] # relays that have reached their position
        self.algorithm         = relayAlg
        self.targetBotsAndData = []
        self.frontiers         = []
        self.allTargets        = []
        self.allPositions      = []
        self.end               = False


        # initial movements
        self._firstMovements()

        for (dotBotId,_) in enumerate(self.dotbotsview):

            self._updateMovement(dotBotId)

        self.allPositions = []

        self.simEngine.schedule(self.simEngine.currentTime(), self._updateFrontiersAndTargets)

    #======================== public ==========================================

    def getExploredCells(self):
        # TODO: store svg rects lazily in cells as their created
        returnVal = {
            'cellsOpen':     [self._hCell2SvgRect(*c) for c in self.path_planner.map.explored],
            'cellsObstacle': [self._hCell2SvgRect(*c) for c in self.path_planner.map.obstacles],
        }
        return returnVal

    #======================== private =========================================

    def _notifyDotBotMoved(self,startX,startY,stopX,stopY):

        # intermediate cells are open

        self.markTraversedCells(startX, startY, stopX, stopY)

        if self.bump == True:
            # stop cell is obstacle
            (x,y) = self._xy2hCell(stopX,stopY)
            self.path_planner.map.add_obstacle(x, y)
            self.path_planner.map.unexplore_cell(x, y)

    def _buildHeatmap(self, cells):
        '''
        builds array with tuples representing (cell position, number of times traversed)
        '''

        # if traversed cell is already in heatmap array just increase number of times cell has been traversed
        # otherwise, add cell to heatmap array then increase number of times cell has been traversed.

        for cell in cells:

            if cell in [h[0] for h in self.heatmap] :

                maxTimesCellTraversed = [h[1] for h in self.heatmap
                 if (h[0] == cell)]
                index = self.heatmap.index((cell, maxTimesCellTraversed[0]))
                self.heatmap[index] = (cell, self.heatmap[index][1]+1)

            else:
                self.heatmap += [((cell[0], cell[1]), 0)]
                maxTimesCellTraversed = [h[1] for h in self.heatmap
                 if (h[0] == cell)]
                index = self.heatmap.index((cell, maxTimesCellTraversed[0]))
                self.heatmap[index] = (cell, self.heatmap[index][1]+1)

    def _updateMovement(self, dotBotId):
        '''
        \post modifies the movement directly in dotbotsview
        '''

        dotbot                  = self.dotbotsview[dotBotId]               # shorthand
        centreCellcentre        = self._xy2hCell(dotbot['x'],dotbot['y'])  # centre point of cell dotbot is in
        target                  = dotbot['target']                         # set target as las allocated target until updated

        self._getRelayBots(self.dotbotsview)
        self.mapBuilder.numDotBots   = self.numDotBots
        self.mapBuilder.numRelayBots = len(self.positionedRelays)

        if centreCellcentre in self.allTargets:
            try:
                self.allTargets.remove(target)
            except ValueError:
                pass

        while True:
            # keep going towards same target if target hasn't been explored yet

            if (target                                                               and
               (target not in self.path_planner.map.explored and target not in self.path_planner.map.obstacles) and
               (dotbot['ID'] in self.positionedRelays) and dotbot['speed'] != -1) :

                # TODO: this should read like plain English
                # TODO: relay status should be a dotbot attribute (e.g. dotbot.relay_status() -> Enum: None, Unpositioned, Positioned, Ready)
                #       so we're not always ensuring clean popping out of and insertion into sets
                # TODO: cell object (i.e. target) should also probably be an object that you can check status of
                #       e.g. target.open and target.obstacle are valid --> target = self.cell(*coordinates)

                if centreCellcentre == target and dotbot['ID'] in self.positionedRelays:
                    # NOTE: Relay DotBot has reached its target and we make it a ready relay
                    # store new movement
                    dotbot['speed'] = -1
                    self.readyRelays += [dotbot['ID']] # FIXME: this is linear in the number of dotbots
                    return

                if self.movingDuration == 0:
                    # NOTE: this path doesn't work, find another one -- why is this a class state
                    #       and not per dotbot state? could be called directly after receiveNotification

                    # avoid these cells when finding new path to target
                    self.hCellsUnreachable += [dotbot['previousPath'][0]]

                path2target             = self.path_planner.computePath(centreCellcentre,target)
            elif (dotbot in self.relayBots):
                target = self._getRelayPosition(dotbot)
                if not target:
                    self.relayBots.remove(dotbot)
                    target = dotbot['target']
                    continue
                else:
                    path2target = self.path_planner.computePath(centreCellcentre, target) # NOTE: just go directly to the target in a line - not anymore, just runs path planner
            else:
                if self.allPositions:
                    target     = self.allPositions[dotBotId]
                else:
                    if self.allTargets:
                        target = self._findBestTarget(centreCellcentre)
                    else:
                        target = None

                try:
                    self.allTargets.remove(target)
                except ValueError:
                    pass

                if not target:
                    print('RETURNING', dotBotId, self.allTargets, self.simEngine.currentTime())
                    dotbot['ID']     = dotBotId
                    dotbot['target'] = centreCellcentre
                    dotbot['timer']  = None
                    dotbot['speed']  = 1
                    dotbot['seqNumMovement'] += 1

                    return # TODO: define expected behavior, better to break than just randomly return, prone to bugs

                if self.end:
                    return # TODO: define expected behavior, better to break than just randomly return, prone to bugs

                if self.allPositions:
                    path2target = [target]
                else:
                    path2target = self.path_planner.computePath(centreCellcentre, target)

                self.hCellsUnreachable = []  # clear out unreachable cells associated with path to previous target

            if path2target:
                break

        #Find headings and time to reach next step, for every step in path2target

        pathHeadings=[]

        for (idx,nextCell) in enumerate(path2target):
            if idx == 0:
                (x,y)    = (dotbot['x'], dotbot['y'])
            else:
                (x,y)    = path2target[idx-1]     # shorthand

            (tx,ty)       = nextCell

            heading       = (math.degrees(math.atan2(ty-y,tx-x))+90) % 360
            timeStep      = u.distance((x,y),(tx,ty))
            pathHeadings += [(heading,timeStep)]

        # Find duration of movement in the same direction

        timeTillStop    = 0

        for (idx,h) in enumerate(pathHeadings):
            if pathHeadings[idx][0] == pathHeadings[0][0]:
                timeTillStop += pathHeadings[idx][1]
            else:
                break

        # store new movement
        dotbot['ID']              = dotBotId
        dotbot['target']          = target
        dotbot['heading']         = pathHeadings[0][0]
        dotbot['timer']           = timeTillStop
        dotbot['previousPath']    = path2target
        dotbot['speed']           = 1
        dotbot['seqNumMovement'] += 1
        dotbot['heartbeat']       = self.heartbeat
        dotbot['pdrHistory']      += [(self.heartbeat,(dotbot['x'],dotbot['y']))]

    def markTraversedCells(self, startX, startY, stopX, stopY): # TODO: unit test
        # scan horizontally
        x_sign = 2 * int(startX < stopX) - 1
        y_sign = 2 * int(startY < stopX) - 1

        step_size = MapBuilder.MINFEATURESIZE_M/2

        x = startX
        while True:
            x += x_sign * step_size
            if (x > stopX if x_sign == 1 else x < stopX):
                break

            y = startY + (((stopY-startY) * (x-startX)) / (stopX-startX))

            (cx,cy) = self._xy2hCell(x,y)
            self.path_planner.map.explore_cell(cx, cy)

        # scan vertically
        y = startY
        while True:
            y += y_sign * step_size
            if (y > stopY if y_sign == 1 else y < stopY):
                break

            x  = startX+(((stopX-startX)*(y-startY))/(stopY-startY))

            (cx,cy) = self._xy2hCell(x,y)
            self.path_planner.map.explore_cell(cx, cy)

    def _rankHopNeighbourhood(self, c0, distanceRank):

        rankHopNeighbours = []

        # shorthand
        (c0x,c0y) = c0

        # 8 cells surround c0, as we expand, distance rank increases, number of surrounding cells increase by 8
        numberOfSurroundingCells = 8 * distanceRank

        # Use angle between center cell and every surrounding cell if cell centres were to be connected by a line
        # find centres of surrounding cells based on DotBot speed and angle
        # assuming it takes 0.5 second to move from half-cell centre to half-cell centre.
        for idx in range(numberOfSurroundingCells):
            (x, y) = u.computeCurrentPosition(c0x, c0y,
                                              ((360 / numberOfSurroundingCells) * (idx + 1)),
                                              1,  # assume speed to be 1 meter per second
                                              0.5*distanceRank)  # duration to move from hcell to hcell = 0.5 seconds

            (scx,scy) = self._xy2hCell(x, y)
            rankHopNeighbours += [(scx,scy)]

        return rankHopNeighbours

    def _findFrontierBoundary(self):
        self.frontiers  = []

        xs = [c[0] for c in self.path_planner.map.explored]
        ys = [c[1] for c in self.path_planner.map.explored]

        minX = min(xs)
        maxX = max(xs)
        minY = min(ys)
        maxY = max(ys)

        for c in self.path_planner.map.explored:
            if c[0] >= minX and c[0] <= maxX and c[1] >= minY and c[1] <= maxY:
                self.frontiers += [c]

        if not self.frontiers:
            self.end = True

    def _findTargets(self):
        for f in self.frontiers:
            for cell in self.path_planner.map.neighbors(self.path_planner.map.cell(*f, local=False)):
                if not cell.explored:
                    self.allTargets.append(cell.position(_local=False))
                else:
                    pass

        self.allTargets = list(set(self.allTargets))

    def _updateFrontiersAndTargets(self):

        if not self.allPositions:
            self._findFrontierBoundary()
            self._findTargets()

        self.simEngine.schedule(self.simEngine.currentTime() + 1, self._updateFrontiersAndTargets)

    def _findBestTarget(self, dbpos):

        targetsAndDistances2db = []

        for t in self.allTargets:
            targetsAndDistances2db += [(t,u.distance(dbpos,t))]

        closestTarget = sorted(targetsAndDistances2db, key=lambda item: item[1])[0][1]
        closestTargets2start = [(c,d) for (c,d) in targetsAndDistances2db if d == closestTarget]

        closestTarget2start = sorted(closestTargets2start, key=lambda item: item[1])[0][1]
        target = [c for (c, d) in closestTargets2start if d == closestTarget2start][0]

        return  target


    def _firstMovements(self):

        start     = (self.ix,self.iy)
        rank      = 1
        numRobots = len(self.dotbotsview)
        while len(self.allPositions) <= numRobots:
            for pos in self._rankHopNeighbourhood(start,rank):
                self.allPositions += [pos]
            rank += 1
        self.allPositions = list(set(self.allPositions))

        return

    def _xy2hCell(self,x,y):

        xsteps = int(round((x-self.ix)/ (MapBuilder.MINFEATURESIZE_M/2),0))
        cx     = self.ix+xsteps*(MapBuilder.MINFEATURESIZE_M/2)
        ysteps = int(round((y-self.iy)/ (MapBuilder.MINFEATURESIZE_M/2),0))
        cy     = self.iy+ysteps*(MapBuilder.MINFEATURESIZE_M/2)

        return (cx,cy)

    def _hCell2SvgRect(self,cx,cy):
        returnVal = {
            'x':        cx-MapBuilder.MINFEATURESIZE_M/4,
            'y':        cy-MapBuilder.MINFEATURESIZE_M/4,
            'width':    MapBuilder.MINFEATURESIZE_M/2,
            'height':   MapBuilder.MINFEATURESIZE_M/2,
        }
        return returnVal

    #################################### Relay Placement Algorithms ###################################################

    def _getRelayBots(self, allDotBots):
        if self.algorithm == 'recovery':
            self._recovery_getRelayBots(allDotBots)
        elif self.algorithm == 'naive':
            self._naive_getRelayBots(allDotBots)
        elif self.algorithm == 'selfHealing':
            self._selfHealing_getRelayBots(allDotBots)

    def _getRelayPosition(self, relayBot):
        if self.algorithm == 'recovery':
            return self._recovery_getRelayPosition(relayBot)
        if self.algorithm == 'naive':
            return self._naive_getRelayPosition(relayBot)
        if self.algorithm == 'selfHealing':
            return self._selfHealing_getRelayPosition(relayBot)

    ######## Recovery Algorithm

    def _recovery_getRelayBots(self, allDotBots):

        for db in allDotBots:
            if db['heartbeat'] < 0.7 and db['heartbeat'] > 0 :
                if db not in self.relayBots:
                    self.relayBots += [db]
                    return

        return

    def _recovery_getRelayPosition(self, relayBot):
        x = None
        y = None

        #pdrHistory = sorted(relayBot['pdrHistory'], key=lambda item: item[1][1])
        pdrHistory = relayBot['pdrHistory']
        pdrHistoryReversed = pdrHistory[::-1]
        for value in pdrHistoryReversed:
            if  value[0] >= 1-(len(self.positionedRelays)/10) :
                bestPDRposition = value[1]
                x = bestPDRposition[0]
                y = bestPDRposition[1]
                break

        if not x and not y:
            return

        for p in self.relayPositions:
            if (x>= (p[0] - 10) and x<= (p[0] + 10)) and ((y >= (p[1] - 10) and y<= (p[1] + 10))):
                return

        if (x,y) not in self.path_planner.map.obstacles and (x,y) not in self.relayPositions and (x,y) not in self.hCellsUnreachable:
            self.relayPositions += [(x,y)]
            self.positionedRelays += [relayBot['ID']]
            return (x, y)

    ######## Naïve Algorithm

    def _naive_getRelayBots(self, allDotBots):
        overlayGridSize = len(self.path_planner.map.explored) + len(self.path_planner.map.obstacles)
        if ((overlayGridSize % 200 == 0)                    and
            (len(self.relayBots) < (overlayGridSize/200))     ):
            self.relayBots += [random.choice(allDotBots)]
        return

    def _naive_getRelayPosition(self, relayBot):
        x = relayBot['x']
        y = relayBot['y']
        self.relayPositions += [(x, y)]
        self.positionedRelays += [relayBot['ID']]
        return (x,y)

    ######## Self-Healing Algorithm
    def _selfHealing_getRelayBots(self, allDotBots):
        distances = []

        needRelay = False
        for d in allDotBots:
            distanceOrchToRobot = u.distance((d['x'],d['y']),(self.ix,self.iy))
            if distanceOrchToRobot >= 30:
                needRelay = True
            else:
                continue

            if self.relayPositions:
                distances += [u.distance((d['x'],d['y']),rp) for rp in self.relayPositions]
                for distance in distances:
                    if distance <= 30:
                        needRelay = False
                        break

            if needRelay == True:
                if self.targetBotsAndData and d in [t['targetBot'] for t in self.targetBotsAndData]:
                    tb = [tb for tb in self.targetBotsAndData if tb['targetBot'] == d][0]
                    x = ((d['x'] + tb['relayPositions'][-1][0])/2)
                    y = ((d['y'] + tb['relayPositions'][-1][1])/2)

                    relayPosition = (x ,y)
                    tb['relayPositions'] += [relayPosition]
                    #print('---', self.targetBotsAndData)
                else:
                    x = ((d['x'] + self.ix)/2)
                    y = ((d['y'] + self.iy)/2)
                    self.targetBotsAndData += [ {'targetBot':d, 'relayPositions' : [(x , y)]} ]
                    #print('+++', self.targetBotsAndData)


                self.relayBots += [random.choice([db for db in allDotBots if (db != d)])]
                #print(self.relayBots)
                #break

        return

    def _selfHealing_getRelayPosition(self, relayBot):
        #print(self.targetBotsAndData)
        #print('.....')
        targetChosen = random.choice(self.targetBotsAndData)

        (xp,yp) = targetChosen['relayPositions'][-1]
        (x,y)   = self._xy2hCell(xp,yp)
        if (x,y) not in self.relayPositions and (x,y) not in self.path_planner.map.obstacles and (x,y) not in self.hCellsUnreachable:
            self.relayPositions += [targetChosen['relayPositions'][-1]]
            self.positionedRelays += [relayBot['ID']]
            return (x,y)
        else:
            return

class Orchestrator(Wireless.WirelessDevice):
    '''
    The central orchestrator of the expedition.
    '''

    COMM_DOWNSTREAM_PERIOD_S   = 1

    def __init__(self, numDotBots, initialPosition, navAlgorithm, relayAlg, wireless=Wireless.WirelessBase):

        # store params
        self.numDotBots        = numDotBots
        self.initialPosition   = initialPosition
        self.relayAlg          = relayAlg

        # local variables
        self.simEngine          = SimEngine.SimEngine()
        self.wireless           = wireless()
        navigationclass         = getattr(sys.modules[__name__],'Navigation{}'.format(navAlgorithm))
        self.navigation         = navigationclass(self.numDotBots, self.initialPosition, relayAlg=self.relayAlg)
        self.communicationQueue = []
    
    #======================== public ==========================================

    #=== admin
    
    def startExploration(self):
        '''
        Simulation engine hands over control to orchestrator
        '''
        
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

        allMovements = self.navigation.getMovements()

        self.communicationQueue += allMovements

        for i in range(0,int(len(allMovements)/self.COMMANDSIZE)+1):

                command = self.communicationQueue[:self.COMMANDSIZE]
                numOfRemainingElements = (len(self.communicationQueue)-self.COMMANDSIZE)
                self.communicationQueue = self.communicationQueue[-numOfRemainingElements:]

                # format frame to transmit
                frameToTx = {
                    'frameType': self.FRAMETYPE_COMMAND,
                    'movements': command
                }


                # hand over to wireless
                self.wireless.transmit(
                    frame  = frameToTx,
                    sender = self,
                )


    
    def receive(self,frame):
        '''
        Notification received from a DotBot.
        '''
        assert frame['frameType']==self.FRAMETYPE_NOTIFICATION

        
        # hand received frame to navigation algorithm
        self.navigation.receiveNotification(frame)
    
    #=== UI
    
    def getView(self):
        '''
        Retrieves the approximate location of the DotBot for visualization.
        '''
        
        returnVal = {
            'dotbotpositions':    self.navigation.getEvaluatedPositions(),
            'discomap':           self.navigation.mapBuilder.getMap(),
            'exploredCells':      self.navigation.getExploredCells(),
        }
        
        return returnVal
    
    #======================== private =========================================
