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
        self.datacollector      = DataCollector.DataCollector()
        self.cellsExplored      = []
        self.cellsObstacle      = []
        self.cellsFrontier      = []

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
            if cellsExplored['nextCell'] in self.cellsFrontier:
                self.cellsFrontier.remove(cellsExplored['nextCell'])

        for cell in self.cellsExplored:
            if cell in self.cellsFrontier:
                self.cellsFrontier.remove(cell)

        for (cx, cy) in cellsExplored['cellsExplored']:
            for n in self._computeCellNeighbours(cx, cy):
                if (
                    (n not in self.cellsExplored) and
                    (n not in self.cellsObstacle)
                ):
                    self.cellsFrontier += [n]

        # remove duplicate cells
        self.cellsObstacle = list(set(self.cellsObstacle))
        self.cellsExplored = list(set(self.cellsExplored))
        self.cellsFrontier = list(set(self.cellsFrontier))
        # update dotBotsView
        dotBot['x']       = newX
        dotBot['y']       = newY
        log.debug(f'dotbot {dotBot} is at ( {newX},{newY} ) ')

        # pick new speed and heading for dotBot
        (heading, speed)  = self._pickNewMovement(frame['source'])
        dotBot['heading'] = heading
        dotBot['speed']   = speed

    #=== Map

    def _computeCellsExplored(self, startX, startY, stopX, stopY):
        '''
        find cells passed through on trajectory between points a and b
        example input - output :
            {
            'in': {
                'startX': 1.10,
                'startY': 1.20,
                'stopX': 2.20,
                'stopY': 1.01,
            },
            'out': {
                'cellsExplored': [(1.00,1.00), (1.50, 1.00), (2.00, 1.00)],
                 nextCell: (2.50, 1.00)
            }
        }
        '''

        returnVal = {'cellsExplored': [], 'nextCell': None}

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

        # maxNumCells is length of line *2 as each cell is 1/2 the size of a unit step
        # we add an extra 2 cells: 1 - in case start cell is not the initial cell and
        # 1 - for when we calculate the next cell beyond the trajectory
        maxNumCells = u.distance((startX, startY), (stopX, stopY))*2 + 2

        # movement is not on boundaries
        if not(
            (startX == stopX) and (startX == cx or startX == cx+self.MINFEATURESIZE/2) or
            (startY == stopY) and (startY == cy or startX == cy+self.MINFEATURESIZE/2)
        ):
            returnVal['cellsExplored'] += [(cx, cy)]
            cellsExploredComputed = False

            if startX == stopX:

                # vertical line, move up or down
                while cellsExploredComputed == False:
                    xmax  = cx + self.MINFEATURESIZE/2
                    ymax  = cy + self.MINFEATURESIZE/2

                    if (
                        cx <= stopX <= xmax and
                        cy <= stopY <= ymax
                    ):
                        cellsExploredComputed = True

                    if startY < stopY:
                        cy = cy + self.MINFEATURESIZE/2
                    else:
                        cy = cy - self.MINFEATURESIZE/2
                    returnVal['cellsExplored'] += [(cx, cy)]

                    log.debug('num cells {} and maxCellNum = {}'.format(len(returnVal['cellsExplored']),abs(maxNumCells)))
                    assert len(returnVal) <= maxNumCells

            else:

                # move according to line equation y = mx + c
                m  = (stopY - startY)/(stopX - startX)
                c  = startY - m*startX
                log.debug(f'stop condition is {self._xy2cell(stopX, stopY)}')

                while cellsExploredComputed == False:

                    ymin = cy
                    ymax = cy + self.MINFEATURESIZE/2
                    xmax = (cx + self.MINFEATURESIZE/2)

                    if startX < stopX:
                        # movement towards right side
                        ynext = m*xmax + c
                        slope = 1
                    else:
                        # movement towards left side
                        ynext = m * cx + c
                        slope = -1

                    log.debug(f'xmax,ymax {xmax}, {ymax}')
                    log.debug(f'ynext {ynext}')

                    if (
                        cx <= stopX <= xmax and
                        cy <= stopY <= ymax
                    ):
                        cellsExploredComputed = True

                    if ynext < ymin:
                        # move up
                        cy = cy - self.MINFEATURESIZE/2
                        returnVal['cellsExplored'] += [(cx, cy)]
                        log.debug(f'move up to -> {(cx, cy)}')

                    elif ymax < ynext:
                        # move down
                        cy = cy + self.MINFEATURESIZE/2
                        returnVal['cellsExplored'] += [(cx, cy)]
                        log.debug(f'move down to -> {(cx, cy)}')

                    elif ynext == ymin:
                        # move diagonally upwards
                        cx = cx + (self.MINFEATURESIZE/2)*slope
                        cy = cy -  self.MINFEATURESIZE/2
                        returnVal['cellsExplored'] += [(cx, cy)]
                        log.debug(f'move diagonally upwards to -> {(cx, cy)}')

                    elif ynext == ymax:
                        # move diagonally downwards
                        cx = cx + (self.MINFEATURESIZE/2)*slope
                        cy = cy +  self.MINFEATURESIZE/2
                        returnVal['cellsExplored'] += [(cx, cy)]
                        log.debug(f'move diagonally downwards to -> {(cx, cy)}')
                    else:
                        # move sideways
                        cx = cx + (self.MINFEATURESIZE/2)*slope
                        returnVal['cellsExplored'] += [(cx, cy)]
                        log.debug(f'move right to -> {(cx, cy)}')

                    log.debug(f'num cells {len(returnVal)} and maxCellNum = {abs(maxNumCells)}')
                    assert len(returnVal) <= maxNumCells

            returnVal['nextCell'] = returnVal['cellsExplored'].pop(-1)

        log.debug(f'new cells {returnVal}')


        return returnVal

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
            'discomap':        {"complete": False, "dots": [], "lines": []},
            'exploredCells':   {
                'cellsExplored': [self._cell2SvgRect(*c) for c in self.cellsExplored],
                'cellsObstacle': [self._cell2SvgRect(*c) for c in self.cellsObstacle],
                'cellsFrontier': [self._cell2SvgRect(*c) for c in self.cellsFrontier],
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

    def _computeCellNeighbours(self, cx, cy):
        cellSize = self.MINFEATURESIZE/2

        returnVal = [
            (cx+cellSize, cy),          (cx-cellSize, cy),
            (cx,          cy-cellSize), (cx,          cy+cellSize),
            (cx-cellSize, cy-cellSize), (cx+cellSize, cy+cellSize),
            (cx-cellSize, cy+cellSize), (cx+cellSize, cy-cellSize)
        ]

        return returnVal