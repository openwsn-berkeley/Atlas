# built-in
import random
import threading
import copy
import sys
import math
import logging

# third-party
# local
import SimEngine
import Wireless
import Utils as u


# logging
log = logging.getLogger('Orchestrator')

class ExceptionOpenLoop(Exception):
    pass

class MapBuilder(object):
    '''
    A background task which consolidates the map.
    It combines dots into lines
    It declares when the map is complete.
    '''

    HOUSEKEEPING_PERIOD_S    = 1    # in simulated time
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

class Navigation(object):

    def __init__(self, numDotBots, initialPosition):

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


            } for [id,(x,y)] in enumerate([self.initialPosition]*self.numDotBots)
        ]
        self.mapBuilder       = MapBuilder()
        self.movingDuration   = 0
        self.heatmap          = [(self.initialPosition, 0)]
        self.profile          = []
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

    #======================== private =========================================

    def _notifyDotBotMoved(self,oldX,oldY,newX,newY):
        raise SystemError('abstract method')

    def _updateMovement(self,dotBotId):
        raise SystemError('abstract method')

class Navigation_Ballistic(Navigation):

    def __init__(self, numDotBots, initialPosition):

        # initialize parent
        super().__init__(numDotBots, initialPosition)

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

class Navigation_Atlas(Navigation):

    def __init__(self, numDotBots, initialPosition):

        # initialize parent
        super().__init__(numDotBots, initialPosition)

        # (additional) local variables
        # shorthands for initial x,y position
        self.ix                = initialPosition[0]
        self.iy                = initialPosition[1]
        # a "half-cell" is identified by its center, and has side MINFEATURESIZE_M/2
        self.hCellsOpen        = []
        self.hCellsObstacle    = []
        self.hCellsUnreachable = []
        # the hCell the DotBot start is in, by definition, open
        self.hCellsOpen       += [initialPosition]
        self.relayBots         = []
        # initial movements
        for (dotBotId,_) in enumerate(self.dotbotsview):
            self._updateMovement(dotBotId)

    #======================== public ==========================================

    def getExploredCells(self):
        returnVal = {
            'cellsOpen':     [self._hCell2SvgRect(*c) for c in self.hCellsOpen],
            'cellsObstacle': [self._hCell2SvgRect(*c) for c in self.hCellsObstacle],
        }
        return returnVal

    def getHeatmap(self):
        heatMapXMax   = sorted(self.heatmap, key=lambda item: item[0][0])[-1][0][0] + 1
        heatMapYMax   = sorted(self.heatmap, key=lambda item: item[0][1])[-1][0][1] + 1
        heatMapXMin   = sorted(self.heatmap, key=lambda item: item[0][0])[0][0][0]
        heatMapYMin   = sorted(self.heatmap, key=lambda item: item[0][1])[0][0][1]

        heatmapValues = []
        overlayGrid    = []

        for r in range(int(heatMapYMax)*2):
            heatmapValues += [[]]
            overlayGrid    += [[]]
            for c in range(int(heatMapXMax)*2):
                heatmapValues[r] += [0]
                overlayGrid[r]    += '-'

        for h in self.heatmap:
            x     = h[0][0]
            y     = h[0][1]
            value = h[1]

            if x >= heatMapXMax or y >= heatMapYMax:
                continue

            heatmapValues[int(y*2)][int(x*2)] = value
            if (x,y) in self.hCellsObstacle:
                overlayGrid[int(y * 2)][int(x * 2)] = '#'
            if (x,y) in self.hCellsOpen:
                overlayGrid[int(y * 2)][int(x * 2)] = '.'
            if (x,y) == self.initialPosition:
                overlayGrid[int(y * 2)][int(x * 2)] = 'S'

        overlayGridJoint = []

        for (i,r) in enumerate(overlayGrid):
            overlayGridJoint += ''.join('\n')
            overlayGridJoint += ''.join(r)

        overlayGridJoint = ''.join(i for i in overlayGridJoint)
        return (heatmapValues,overlayGridJoint)

    def getProfile(self):
        return self.profile
    #======================== private =========================================

    def _notifyDotBotMoved(self,startX,startY,stopX,stopY):

        # intermediate cells are open

        traversedCells   = self._cellsTraversed(startX,startY,stopX,stopY)
        self.hCellsOpen += traversedCells

        if self.bump == True:
            # stop cell is obstacle
            (x,y) = self._xy2hCell(stopX,stopY)
            self.hCellsObstacle += [(x, y)]
            traversedCells += [(x,y)]

        self._buildHeatmap(traversedCells)

        # if a cell is obstacle, remove from open cells
        for c in self.hCellsObstacle:
            try:
                self.hCellsOpen.remove(c)
            except ValueError:
                pass

        # filter duplicates in either list
        self.hCellsOpen      = list(set(self.hCellsOpen))
        self.hCellsObstacle  = list(set(self.hCellsObstacle))

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
        self.skip               = False


        while True:
            # keep going towards same target if target hasn't been explored yet

            if (target                                                               and
               (target not in self.hCellsOpen and target not in self.hCellsObstacle) and
                self.skip == False          ):

                if self.movingDuration == 0:
                    # avoid these cells when finding new path to target
                    self.hCellsUnreachable += [dotbot['previousPath'][0]]

                path2target               = self._path2Target(centreCellcentre,target)

            else:

                if dotbot in self._getRelayBots(self.dotbotsview):
                    if centreCellcentre == target:
                        # store new movement
                        dotbot['ID'] = dotBotId
                        dotbot['target'] = None
                        dotbot['heading'] = None
                        dotbot['timer'] = 0
                        dotbot['previousPath'] = None
                        dotbot['speed'] = -1
                        dotbot['seqNumMovement'] += 1
                        dotbot['heartbeat'] = self.heartbeat
                        dotbot['pdrHistory'] += [(self.heartbeat, (dotbot['x'], dotbot['y']))]
                        return
                    else:
                        target = self._getRelayPosition(dotbot)
                        path2target = self._path2Target(centreCellcentre, target)
                else:

                    # if target explored or no paths to target, find a new target

                    # frontier cell is an open cell with at least 1 unexplored cell in its 1-hop neighbourhood
                    # find closest frontier to robot and out of those, closest to the initial position cell

                    frontierCellsAndDistances = self.frontierCellsAndDistances(centreCellcentre)
                    if not frontierCellsAndDistances:   # no more available frontier cells
                        return

                    closestFrontier2Start     = sorted(frontierCellsAndDistances, key=lambda item: item[1])[0][1]
                    frontierCells             = [c for (c,d) in frontierCellsAndDistances if d==closestFrontier2Start]

                    # chose frontier cell
                    frontierCell  = random.choice(frontierCells)

                    # chose target
                    for n in self._oneHopNeighborsShuffled(*frontierCell):
                        if (n not in self.hCellsOpen) and (n not in self.hCellsObstacle):
                            target = n
                            break

                    assert target

                    self.hCellsUnreachable = []   # clear out unreachable cells associated with path to previous target

                    path2target            = self._path2Target(centreCellcentre, target)

            if path2target:
                break
            else:
                if self.skip == False:
                    self.hCellsObstacle += [target]
                continue


        # Find headings and time to reach next step, for every step in path2target
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

    def frontierCellsAndDistances(self, c0):

        start                     = (self.ix,self.iy)  # shorthand
        distanceRank              = 0                  # distance rank between DotBot position and surrounding cell set
        openCells                 = []
        frontierCellsAndDistances = []

        # if cell, dotbot is on (c0), is an open cell and has at least 1 unexplored 1 hop neighbour, take c0 as frontier
        if c0 in self.hCellsOpen and self.hCellsOpen:
            for n in self._oneHopNeighborsShuffled(*c0):
                if (n not in self.hCellsOpen) and (n not in self.hCellsObstacle):
                    f2startDistance = u.distance(c0, start)
                    frontierCellsAndDistances += [(c0, f2startDistance)]
                    return frontierCellsAndDistances

        # if c0 is an obstacle cell, or c0 is an open cell with no unexplored 1 hop neighbours
        # find closest open cells at least 1 unexplored 1-hop neighbours and take them as frontiers
        while not frontierCellsAndDistances:

            distanceRank += 1
            openCells = []

            rankHopNeighbourhood = self._rankHopNeighbourhood(c0, distanceRank)

            for n in rankHopNeighbourhood:
                if n in self.hCellsOpen:
                    openCells += [n]

            # no more frontiers or valid targets
            if not openCells and c0 != start:
                return None

            for (ocx,ocy) in openCells:
                for n in self._oneHopNeighborsShuffled(ocx,ocy):
                    if (n not in self.hCellsOpen) and (n not in self.hCellsObstacle):
                        f2startDistance = u.distance((ocx,ocy), start)
                        frontierCellsAndDistances += [((ocx,ocy),f2startDistance)]
                        break

        return frontierCellsAndDistances

    def _path2Target(self, start, target):
        '''
        A* Algorithm for finding shortest path to target
        '''

        targetBlocked        = None
        openCells            = [{'cellCentre': start, 'gCost': 0, 'hCost': 0, 'fCost':0}]
        closedCells          = []
        parentAndChildCells  = [(None,start)]

        while openCells:

            # if target has no open cells connected to it directly, there is no valid path to target

            for n in self._oneHopNeighborsShuffled(*target):
                if n in self.hCellsOpen:
                    targetBlocked = False
                    break

            if targetBlocked != False and self.hCellsOpen:
                self.skip = True
                return None

            openCells            = sorted(openCells, key=lambda item: item['fCost']) # find open cell with lowest F cost
            parent               = openCells[0]
            currentCell          = parent['cellCentre']
            openCells.pop(0)
            closedCells         += [parent]

            if currentCell == target:              # we have reached target, backtrack direct path
                directPathCells              = []

                while currentCell is not None:
                    directPathCells         += [currentCell]
                    currentCell              = [p[0] for p in parentAndChildCells
                                               if (p[1] == currentCell and p[1] != None)][0]

                directPathCells.reverse()

                if directPathCells[0] == start:     # remove cell robot is in from path
                    directPathCells.pop(0)

                return directPathCells

            for child in self._oneHopNeighborsShuffled(*currentCell):

                # skip neighbour if obstacle or already evaluated (closed)
                if (child in self.hCellsObstacle or
                   (child in self.hCellsUnreachable and child != target)):
                    continue

                gCost  = parent['gCost'] + 1
                hCost  = u.distance(child,target)
                fCost  = gCost + hCost

                # add penalty to avoid choosing target as first step if it was unreachable last time
                if (child == target and target in self.hCellsUnreachable and  gCost == 1 and self.movingDuration == 0):
                    fCost = fCost + 0.5
                    continue

                # don't consider cell if same cell with lower fcost  is already in closed cells
                if (child in [cell['cellCentre'] for cell in closedCells
                    if (cell['cellCentre'] == child and cell['fCost'] <= fCost)]):
                    continue

                # don't consider cell if same cell with lower fcost  is already in open cells
                if (child in [cell['cellCentre'] for cell in openCells
                    if (cell['cellCentre'] == child and cell['fCost'] <= fCost)]):
                    continue

                openCells += [{'cellCentre': child, 'gCost': gCost, 'hCost': hCost, 'fCost': fCost}]
                parentAndChildCells += [(currentCell, child)]

    def _cellsTraversed(self,startX,startY,stopX,stopY):
        returnVal = []

        # scan horizontally
        x         = startX
        while True:

            if startX<stopX:
                # going right
                x += MapBuilder.MINFEATURESIZE_M/2
                if x>stopX:
                    break
            else:
                # going left
                x -= MapBuilder.MINFEATURESIZE_M/2
                if x<stopX:
                    break

            y  = startY+(((stopY-startY)*(x-startX))/(stopX-startX))

            (cx,cy) = self._xy2hCell(x,y)
            returnVal += [(cx,cy)]

        # scan vertically
        y         = startY
        while True:

            if startY<stopY:
                # going down
                y += MapBuilder.MINFEATURESIZE_M/2
                if y>stopY:
                    break
            else:
                y -= MapBuilder.MINFEATURESIZE_M/2
                if y<stopY:
                    break

            x  = startX+(((stopX-startX)*(y-startY))/(stopY-startY))

            (cx,cy) = self._xy2hCell(x,y)
            returnVal += [(cx,cy)]

        # filter duplicates
        returnVal = list(set(returnVal))

        return returnVal

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

    def _oneHopNeighborsShuffled(self,cx,cy):
        s = MapBuilder.MINFEATURESIZE_M/2 # shorthand
        returnVal = [
            (cx-s,cy-s),(cx,cy-s),(cx+s,cy-s),
            (cx-s,cy  )          ,(cx+s,cy  ),
            (cx-s,cy+s),(cx,cy+s),(cx+s,cy+s),
        ]
        random.shuffle(returnVal)
        return returnVal


    def _getRelayBots(self, allDotBots):
        for db in allDotBots:
            if db['heartbeat'] < 0.7 and db['heartbeat'] > 0 :
                self.relayBots += [db]
                break

        return self.relayBots

    def _getRelayPosition(self, relayBot):
        print('++++relayBots+++++', set([r['ID'] for r in self.relayBots]),)
        pdrHistory = relayBot['pdrHistory']
        bestPDRposition = sorted(pdrHistory, key=lambda item: item[0])[-1][1]
        print(relayBot['pdrHistory'])
        print(bestPDRposition)
        x = bestPDRposition[0]
        y = bestPDRposition[1]
        return (x,y)

        # def _getRelayPosition(self, relayBot):
        #     pdrHistory = relayBot['pdrHistory']
        #     bestPDRposition = sorted(pdrHistory, key=lambda item: item[0])[-1][1]
        #     print(bestPDRposition)
        #     return bestPDRposition


    
class Orchestrator(Wireless.WirelessDevice):
    '''
    The central orchestrator of the expedition.
    '''

    COMM_DOWNSTREAM_PERIOD_S   = 1

    def __init__(self,numDotBots,initialPosition,navAlgorithm):

        # store params
        self.numDotBots        = numDotBots
        self.initialPosition   = initialPosition

        # local variables
        self.simEngine          = SimEngine.SimEngine()
        self.wireless           = Wireless.Wireless()
        navigationclass         = getattr(sys.modules[__name__],'Navigation_{}'.format(navAlgorithm))
        self.navigation         = navigationclass(self.numDotBots, self.initialPosition)
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
        self.navigation.profile += [len(self.navigation.hCellsOpen + self.navigation.hCellsObstacle)]
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


                # log
                log.debug('[%10.3f] --> TX command %s',self.simEngine.currentTime(),frameToTx['movements'])

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

        # log
        log.debug('[%10.3f] <-- RX notif %s',self.simEngine.currentTime(),frame)
        
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
