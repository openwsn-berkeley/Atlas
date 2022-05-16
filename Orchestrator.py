# built-in
import random
import math
# third-party
# local
import SimEngine
import Wireless
import Utils as u
import DataCollector

# setup logging
import logging.config
import LoggingConfig
logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)
log = logging.getLogger('Orchestrator')

class ExceptionOpenLoop(Exception):
    pass

class MapBuilder(object):
    '''
    A background task which consolidates the map.
    It combines dots into lines
    It declares when the map is complete.
    '''

    HOUSEKEEPING_PERIOD_S    = 60    # in simulated time
    MINFEATURESIZE_M         = 1.00  # shortest wall, narrowest opening

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

class Orchestrator(Wireless.WirelessDevice):
    '''
    The central orchestrator of the expedition.
    '''
    
    COMM_DOWNSTREAM_PERIOD_S    = 1
    MINFEATURESIZE              = 1
    
    def __init__(self, numRobots, initX, initY):

        # store params
        self.numRobots          = numRobots
        self.initX              = initX
        self.initY              = initY

        # local variables
        self.simEngine          = SimEngine.SimEngine()
        self.wireless           = Wireless.Wireless()
        self.mapBuilder         = MapBuilder()
        self.datacollector      = DataCollector.DataCollector()
        self.cellsExplored      = []
        self.cellsObstacle      = []

        self.dotBotsView        = dict([
            (
                i,
                {
                   'x':                initX,
                   'y':                initY,
                   'heading':          0,
                   'speed':            0,
                }
            ) for i in range(1, self.numRobots+1)
        ])

        # initial movements
        for dotBotId in range(1,self.numRobots+1):
            (heading, speed) = self._pickNewMovement(dotBotId)
            self.dotBotsView[dotBotId]['heading'] = heading
            self.dotBotsView[dotBotId]['speed']   = speed

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

        log.debug(f'dotBotsView -> {self.dotBotsView}')

        frameToTx = {
            'frameType': self.FRAMETYPE_COMMAND,
            'movements': dict([
                (
                    dotBotId,
                    {
                        'heading': dotBot['heading'],
                        'speed':   dotBot['speed'],
                    }
                ) for (dotBotId, dotBot) in self.dotBotsView.items()]
            )
        }

        # hand over to wireless
        self.wireless.transmit(
            frame  = frameToTx,
            sender = self,
        )

    def _pickNewMovement(self, dotBotId):
        '''
        modifies the movement in dotBotsview
        '''

        heading = 360 * random.random()
        speed   = 1

        return (heading, speed)

    def receive(self,frame):
        '''
        Notification received from a DotBot, indicating it has just bumped
        '''

        assert frame['frameType'] == self.FRAMETYPE_NOTIFICATION

        # shorthand
        dotBot       = self.dotBotsView[frame['source']]

        # update DotBot's position
        (newX, newY) = u.computeCurrentPosition(
            currentX = dotBot['x'],
            currentY = dotBot['y'],
            heading  = dotBot['heading'],
            speed    = dotBot['speed'],
            duration = frame['movementDuration'],
        )

        # update explored cells
        cellsExplored          = self._computeCellsExplored(dotBot['x'], dotBot['y'], newX, newY)
        self.cellsExplored    += cellsExplored['cellsExplored']

        if cellsExplored['nextCell'] and self._xy2cell(newX, newY) != (newX, newY):
            self.cellsObstacle  += [cellsExplored['nextCell']]

        # remove duplicate cells
        self.cellsObstacle  = list(set(self.cellsObstacle))
        self.cellsExplored = list(set(self.cellsExplored))

        # update dotBotsView
        dotbot['x']       = newX
        dotbot['y']       = newY
        self.mapBuilder.notifBump(newX, newY)
        log.debug(f'dotbot {dotbot} is at ( {newX},{newY} ) ')

        # pick new speed and heading for dotBot
        (heading, speed)  = self._pickNewMovement(frame['source'])
        dotBot['heading'] = heading
        dotBot['speed']   = speed

    #=== Map

    def _computeCellsExplored(self, ax, ay, bx, by):
        '''
        find cells passed through on trajectory between points a and b
        example input - output :
            {
            'in': {
                'ax': 1.10,
                'ay': 1.20,
                'bx': 2.20,
                'by': 1.01,
            },
            'out': {
                'cellsExplored': [(1.00,1.00), (1.50, 1.00), (2.00, 1.00)],
                nextCell: (2.50, 1.00)
                }
        }
        '''
        returnVal = []

        # set start and stop cells
        (startX, startY) = (ax, ay)
        (stopX, stopY)   = (bx, by)

        # find current cell coordinates
        (cx,cy)      = self._xy2cell(startX, startY)

        # check if current cell is start cell
        if startX == cx or startY == cy:
            if (stopX < startX) and (startX == cx):
                cx = cx - self.MINFEATURESIZE/2
            if (stopY < startY) and (startY == cy):
                cy = cy - self.MINFEATURESIZE/2

        log.debug(f'moving from {startX}, {startY} to {stopX}, {stopY}')
        log.debug(f'next cell -> {(cx, cy)}')

        maxNumCells = ((abs(stopX - startX) + abs(stopY - startY))*4) + 2

        # movement between cells (on boundaries)
        if (
            (startX == stopX) and (startX == cx or startX == cx+self.MINFEATURESIZE/2) or
            (startY == stopY) and (startY == cy or startX == cy+self.MINFEATURESIZE/2)
        ):
            return {'cellsExplored': [], 'nextCell': None}

        returnVal += [(cx, cy)]
        exploredCellsComputed = False

        if startX == stopX:
            # vertical line, move up or down
            while exploredCellsComputed == False:
                xmax  = cx + self.MINFEATURESIZE/2
                ymax  = cy + self.MINFEATURESIZE/2

                if (
                    cx <= stopX <= xmax and
                    cy <= stopY <= ymax
                ):
                    exploredCellsComputed = True

                if startY < stopY:
                    cy = cy + self.MINFEATURESIZE/2
                else:
                    cy = cy - self.MINFEATURESIZE/2
                returnVal += [(cx, cy)]

                log.debug(f'num cells {len(returnVal)} and maxCellNum = {abs(maxNumCells)}')
                assert len(returnVal) <= maxNumCells

        else:

            # move according to line equation y = mx + c
            m  = (by - ay)/(bx - ax)
            c  = startY - m*startX
            log.debug(f'stop condition is {self._xy2cell(stopX, stopY)}')

            while exploredCellsComputed == False:

                ymin = cy
                ymax = cy + self.MINFEATURESIZE/2
                xmax = (cx + self.MINFEATURESIZE/2)

                if stopX > startX:
                    # movement towards right side
                    ynext = m*xmax + c
                    xdirection = 1
                else:
                    # movement towards left side
                    ynext = m * cx + c
                    xdirection = -1

                log.debug(f'xmax,ymax {xmax}, {ymax}')
                log.debug(f'ynext {ynext}')

                if (
                    cx <= stopX <= xmax and
                    cy <= stopY <= ymax
                ):
                    exploredCellsComputed = True

                if ynext < ymin:
                    # move up
                    cy = cy - self.MINFEATURESIZE/2
                    returnVal += [(cx, cy)]
                    log.debug(f'move up to -> {(cx, cy)}')

                elif ynext > ymax:
                    # move down
                    cy = cy + self.MINFEATURESIZE/2
                    returnVal += [(cx, cy)]
                    log.debug(f'move down to -> {(cx, cy)}')

                elif ynext == ymin:
                    # move diagonally upwards
                    cx = cx + (self.MINFEATURESIZE/2)*xdirection
                    cy = cy -  self.MINFEATURESIZE/2
                    returnVal += [(cx, cy)]
                    log.debug(f'move diagonally upwards to -> {(cx, cy)}')

                elif ynext == ymax:
                    # move diagonally downwards
                    cx = cx + (self.MINFEATURESIZE/2)*xdirection
                    cy = cy +  self.MINFEATURESIZE/2
                    returnVal += [(cx, cy)]
                    log.debug(f'move diagonally downwards to -> {(cx, cy)}')
                else:
                    # move sideways
                    cx = cx + (self.MINFEATURESIZE/2)*xdirection
                    returnVal += [(cx, cy)]
                    log.debug(f'move right to -> {(cx, cy)}')

                log.debug(f'num cells {len(returnVal)} and maxCellNum = {abs(maxNumCells)}')
                assert len(returnVal) <= maxNumCells

        log.debug(f'new cells {returnVal}')
        nextCell = returnVal.pop(-1)

        return {'cellsExplored': returnVal, 'nextCell': nextCell}

    #=== UI

    def getEvaluatedPositions(self):
        '''
        Retrieve the evaluated positions of each DotBot.
        '''
        returnVal = [
            {
                'x':         dotBot['x'],
                'y':         dotBot['y'],
            } for dotBotId, dotBot in self.dotBotsView.items()
        ]
        return returnVal

    def getView(self):
        '''
        Retrieves the approximate location of the DotBot for visualization.
        '''

        returnVal = {
            'dotBotpositions': self.getEvaluatedPositions(),
            'discomap':        self.mapBuilder.getMap(),
            'exploredCells':   {
                'cellsExplored': [self._cell2SvgRect(*c) for c in self.cellsExplored],
                'cellsObstacle': [self._cell2SvgRect(*c) for c in self.cellsObstacle],
            },
        }
        
        return returnVal
    
    #======================== private =========================================

    def _xy2cell(self, x, y):

        # convert x,y coordinates to cell (top left coordinate)
        xsteps = int(math.floor((x)/ (self.MINFEATURESIZE/2)))
        cx     = xsteps*(self.MINFEATURESIZE/2)
        ysteps = int(math.floor((y)/ (self.MINFEATURESIZE/2)))
        cy     = ysteps*(self.MINFEATURESIZE/2)

        return (cx, cy)

    def _cell2SvgRect(self,cx,cy):
        returnVal = {
            'x':        cx,
            'y':        cy,
            'width':    self.MINFEATURESIZE/2,
            'height':   self.MINFEATURESIZE/2,
        }
        return returnVal