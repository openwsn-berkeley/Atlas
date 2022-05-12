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
        self.exploredCells      = []
        self.obstacleCells      = []

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
        self.exploredCells  += self._computeCellsTraversed(dotBot['x'], dotBot['y'], newX, newY)

        # update obstacle cells
        self.obstacleCells  += [self._xy2cell(newX, newY)]

        # remove duplicate cells
        self.obstacleCells  = list(set(self.obstacleCells))
        self.exploredCells  = list(set(self.exploredCells))

        # update dotBotsView
        dotBot['x']       = newX
        dotBot['y']       = newY

        # pick new speed and heading for dotBot
        (heading, speed)  = self._pickNewMovement(frame['source'])
        dotBot['heading'] = heading
        dotBot['speed']   = speed


    #=== Map

    def _computeCellsTraversed(self, ax, ay, bx, by):
        '''
        find cells passed through on trajectory between points a and b
        '''
        returnVal = []

        # find start and stop cells
        if ax > bx:
            (startX, startY) = (bx, by)
            (stopX, stopY)   = (ax, ay)
        elif ax == bx and ay > by:
            (startX, startY) = (bx, by)
            (stopX, stopY)   = (ax, ay)
        else:
            (startX, startY) = (ax, ay)
            (stopX, stopY)   = (bx, by)

        (cx,cy)      = self._xy2cell(startX, startY)
        log.debug(f'moving from {startX}, {startY} to {stopX}, {stopY}')
        returnVal += [(cx, cy)]

        log.debug(f'next cell -> {(cx, cy)}')

        maxCellNum = ((abs(math.ceil(stopX - startX)) + abs(math.ceil(stopY - startY)))*4) + 1

        if (((startY == stopY) and
            (ax == cx or ax == cx+self.MINFEATURESIZE/2 or bx == cx or bx == cx+self.MINFEATURESIZE/2)) or
            ((startX == stopX) and
            (ay == cy or ay == cy+self.MINFEATURESIZE / 2 or by == cy or by == cy+self.MINFEATURESIZE/2))):
            return []

        if startX == stopX:

            # vertical line, move down (increase y)
            while True:
                cy += self.MINFEATURESIZE/2
                returnVal += [(cx, cy)]
                log.debug(f'next cell -> {(cx,cy)}')

                if self._xy2cell(cx, cy) == self._xy2cell(stopX, stopY):
                    break

                log.debug(f'num cells {len(returnVal)} and maxCellNum = {abs(maxCellNum)}')
                assert len(returnVal) <= maxCellNum

        else:

            # move according to line equation y = mx + c
            m  = (by - ay)/(bx - ax)
            c  = startY - m*startX
            log.debug(f'stop condition is {self._xy2cell(stopX, stopY)}')

            while True:

                if self._xy2cell(cx, cy) == self._xy2cell(stopX, stopY):
                    break

                xmax  = (cx + self.MINFEATURESIZE/2)
                ynext = m*xmax + c
                ymin  = cy
                ymax  = cy + self.MINFEATURESIZE/2
                log.debug(f'xmax,ymax {xmax}, {ymax}')
                log.debug(f'ynext {ynext}')

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

                elif (ynext == ymin or ynext == ymax):

                    # move diagonally
                    cy = cy + self.MINFEATURESIZE / 2
                    cx = cx + self.MINFEATURESIZE/2
                    returnVal += [(cx, cy)]
                    log.debug(f'move diagonally to -> {(cx, cy)}')

                else:
                    # move right
                    cx = cx + self.MINFEATURESIZE/2
                    returnVal += [(cx, cy)]
                    log.debug(f'move right to -> {(cx, cy)}')

                log.debug(f'num cells {len(returnVal)} and maxCellNum = {abs(maxCellNum)}')
                assert len(returnVal) <= maxCellNum

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
                'cellsOpen':     [self._cell2SvgRect(*c) for c in self.exploredCells],
                'cellsObstacle': [self._cell2SvgRect(*c) for c in self.obstacleCells],
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