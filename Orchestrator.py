# built-in
import random
import threading
import copy
import sys
import math
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
            if  u.distance((l1ax,l1ay),(l2ax,l2ay))<self.MINFEATURESIZE_M:
                returnVal = True
                break
            if  u.distance((l1ax,l1ay),(l2bx,l2by))<self.MINFEATURESIZE_M:
                returnVal = True
                break
            if  u.distance((l1bx,l1by),(l2ax,l2ay))<self.MINFEATURESIZE_M:
                returnVal = True
                break
            if  u.distance((l1bx,l1by),(l2bx,l2by))<self.MINFEATURESIZE_M:
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
                # evaluated position of the DotBot when it last stopped
                'x':                        x,
                'y':                        y,
                # current movement
                'heading':                  0,
                'speed':                    0,
                'seqNumMovement':           0,
                'lastSeqNumNotification':   0,
                'target':                   None,
                'timer':                    None,
                'previousPath':             None,

            } for (x,y) in [self.initialPosition]*self.numDotBots
        ]
        self.mapBuilder      = MapBuilder()
    
    #======================== public ==========================================
    
    def receiveNotification(self,frame):
        '''
        We just received a notification for a DotBot.
        '''
        
        # shorthand
        dotbot = self.dotbotsview[frame['dotBotId']]

        # update DotBot's position
        (newX,newY) = u.computeCurrentPosition(
            currentX = dotbot['x'],
            currentY = dotbot['y'],
            heading  = dotbot['heading'],
            speed    = dotbot['speed'],
            duration = frame['tsMovementStop'] - frame['tsMovementStart'],
        )
        self._notifyDotBotMoved(dotbot['x'],dotbot['y'],newX,newY)
        (dotbot['x'],dotbot['y']) = (newX,newY)

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
                'heading':                   dotbot['heading'],
                'speed':                     dotbot['speed'],
                'seqNumMovement':            dotbot['seqNumMovement'],
                'target':                    dotbot['target'],
                'timer':                     dotbot['timer'],
                'previousPath':              dotbot['previousPath']
            } for dotbot in self.dotbotsview
        ]
        return returnVal

    def receive(self,frame):
        '''
        Notification received from a DotBot.
        '''
        assert frame['frameType']==self.FRAMETYPE_NOTIFICATION

        # hand received frame to navigation algorithm
        self.navigation.receiveNotification(frame)

    def getExploredCells(self):
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
        self.ix              = initialPosition[0]
        self.iy              = initialPosition[1]
        # a "half-cell" is identified by its center, and has side MINFEATURESIZE_M/2
        self.hCellsOpen      = []
        self.hCellsObstacle  = []
        
        # the hCell the DotBot start is in, by definition, open
        self.hCellsOpen     += [initialPosition]
        
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
    
    #======================== private =========================================
    
    def _notifyDotBotMoved(self,startX,startY,stopX,stopY):
        
        # intermediate cells are open
        self.hCellsOpen += self._cellsTraversed(startX,startY,stopX,stopY)
        
        # FIXME : only when bumps happens
        # stop cell is obstacle
        (x,y) = self._xy2hCell(stopX,stopY)
        self.hCellsObstacle += [(x,y)]
        
        # if a cell is obstacle, remove from open cells
        for c in self.hCellsObstacle:
            try:
                self.hCellsOpen.remove(c)
            except ValueError:
                pass
        
        # filter duplicates in either list
        self.hCellsOpen      = list(set(self.hCellsOpen))
        self.hCellsObstacle  = list(set(self.hCellsObstacle))
    
    def _updateMovement(self, dotBotId):
        '''
        \post modifies the movement directly in dotbotsview
        '''

        # shorthand
        dotbot                 = self.dotbotsview[dotBotId]
        centreCellcentre       = self._xy2hCell(dotbot['x'],dotbot['y'])  # centre point of cell dotbotis in
        avaliableTargetCells   = [] # cells that are closest to DotBot and are unexplored
        distanceRank           = 0  # distance rank between DotBot position and surrounding cell set
        target                 = None

        if ((dotbot['target'] in self.hCellsOpen or dotbot['target'] in self.hCellsObstacle)
                or centreCellcentre == (self.ix, self.iy)):
            # Chose next target cell to move to
            while True:
                distanceRank += 1

                avaliableTargetCells += self._rankHopNeighbourhood(centreCellcentre,distanceRank)

                if avaliableTargetCells:
                    break

            assert  avaliableTargetCells
            target = random.choice(avaliableTargetCells)
            path2target = self._path2Target(centreCellcentre, target)

        else:
            target = dotbot['target']
            # Find shortest path to reach target destination
            path2target           = self._path2Target(centreCellcentre,target, dotbot['previousPath'])

        assert len(path2target)>1
        path2target.pop(0)

        # Find headings to reach each cell on path2target
        pathHeadings=[]
        for nextCell in path2target:
            (tx,ty) = nextCell # shorthand
            x       = dotbot['x']
            y       = dotbot['y']
            heading = (math.degrees(math.atan2(ty-y,tx-x))+90) % 360
            pathHeadings += [heading]

        # Find Timer duration (time till stop) for each heading
        pathTimers = []
        for idx in range(len(pathHeadings)):
            timeTillStop = 0.5   # takes 0.5 seconds to move from cell centre to cell centre
            if idx>0 and (pathHeadings[idx] == pathHeadings[idx-1]):
                pathHeadings.pop(idx-1)
                pathTimers.pop(idx-1)
                timeTillStop += 0.5
            pathTimers += [timeTillStop]

        headingsAndTimers2Target = list(zip(pathHeadings,pathTimers))

        # store new movement
        dotbot['target'] = target
        dotbot['heading']         = headingsAndTimers2Target[0][0]
        dotbot['timer']           = headingsAndTimers2Target[0][1]
        dotbot['previousPath']    = path2target
        dotbot['speed']           = 1
        dotbot['seqNumMovement'] += 1


    def _rankHopNeighbourhood(self, c0, distanceRank):

        avaliableTargetCells = []

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

            if ((scx,scy)  not in self.hCellsOpen) and ((scx,scy)  not in self.hCellsObstacle):
                #if self._path2Target(c0, (scx,scy)):
                avaliableTargetCells += [(scx,scy) ]

        return avaliableTargetCells

    def _path2Target(self, start, target,path2Avoid=None):
        '''
        A* Algorithm for finding shortest path to target
        '''

        openCells            = [{'cellCentre': start, 'gCost': 0, 'hCost': 0, 'fCost':0}]
        closedCells          = []
        parentAndChildCells = [(None,start)]

        while openCells:

            # find open cell with lowest F cost
            openCells = sorted(openCells, key=lambda item: item['fCost'])
            parent               = openCells[0]
            currentCell          = parent['cellCentre']
            openCells.pop(0)
            closedCells         += [parent]


            if currentCell == target: # we have reached target, backtrack direct path
                directPathCells              = []

                while currentCell is not None:
                    directPathCells         += [currentCell]
                    currentCell              = [p[0] for p in parentAndChildCells
                                               if (p[1] == currentCell and p[1] != None)][0]

                directPathCells.reverse()
                return directPathCells

            for child in self._oneHopNeighborsShuffled(*currentCell):
                # skip neighbour if obstacle or already evaluated (closed)
                if (child in self.hCellsObstacle):
                    continue

                gCost  = parent['gCost'] + 1
                hCost  = u.distance(child,target)
                fCost  = gCost + hCost


                if (child in [cell['cellCentre'] for cell in closedCells
                    if (cell['cellCentre'] == child and cell['fCost'] <= fCost)]):
                    continue

                if (child in [cell['cellCentre'] for cell in openCells
                    if (cell['cellCentre'] == child and cell['fCost'] <= fCost)]):
                    continue

                if path2Avoid:
                    if gCost<= len(path2Avoid) and path2Avoid[gCost-1] == child:
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
        self.simEngine         = SimEngine.SimEngine()
        self.wireless          = Wireless.Wireless()
        navigationclass        = getattr(sys.modules[__name__],'Navigation_{}'.format(navAlgorithm))
        self.navigation        = navigationclass(self.numDotBots, self.initialPosition)
    
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

        # format frame to transmit
        frameToTx = {
            'frameType': self.FRAMETYPE_COMMAND,
            'movements': self.navigation.getMovements(),
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
