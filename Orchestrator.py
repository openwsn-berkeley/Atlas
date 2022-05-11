# built-in
import abc
import random
import threading
import copy
import sys
import math
import typing
import time
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

        log.debug(f'dotbotsView -> {self.dotBotsView}')

        frameToTx = {
            'frameType': self.FRAMETYPE_COMMAND,
            'movements': dict([
                    (
                        dotBotId,
                        {
                           'heading': dotbot['heading'],
                           'speed':   dotbot['speed'],
                        }
                    ) for (dotBotId, dotbot) in self.dotBotsView.items()]
            )
        }

        # hand over to wireless
        self.wireless.transmit(
            frame  = frameToTx,
            sender = self,
        )

    def _pickNewMovement(self, dotBotId):
        '''
        modifies the movement in dotbotsview
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
        dotbot       = self.dotBotsView[frame['source']]
        log.debug('dotbot {} was at ( {},{} ) '.format(dotbot, dotbot['x'], dotbot['y']))

        # update DotBot's position
        (newX, newY) = u.computeCurrentPosition(
            currentX = dotbot['x'],
            currentY = dotbot['y'],
            heading  = dotbot['heading'],
            speed    = dotbot['speed'],
            duration = frame['movementDuration'],
        )

        # update explored cells
        self.obstacleCells  += [self._xy2hCell(newX, newY)]
        cellsTraversed       = self._computeCellsTraversed(dotbot['x'], dotbot['y'], newX, newY)
        self.exploredCells  += [c for c in cellsTraversed if c not in self.obstacleCells]

        # if a cell is obstacle, remove from open cells
        try:
            self.exploredCells.remove(self._xy2hCell(newX, newY))
        except ValueError:
            pass

        # remove duplicate cells
        self.obstacleCells  = list(set(self.obstacleCells))
        self.exploredCells      = list(set(self.exploredCells))

        # update dotBotsView
        dotbot['x']       = newX
        dotbot['y']       = newY

        # pick new speed and heading for dotbot
        (heading, speed)  = self._pickNewMovement(frame['source'])
        dotbot['heading'] = heading
        dotbot['speed']   = speed


    #=== Map

    def _computeCellsTraversed(self, ax, ay, bx, by):
        '''
        find cells on trajectory between points a and b
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

        (x,y)      = self._xy2hCell(startX, startY)
        log.debug(f'moving from {startX}, {startY} to {stopX}, {stopY}')
        returnVal += [(x, y)]

        # return current cell if still in same cell
        if self._xy2hCell(startX, startY) == self._xy2hCell(stopX, stopY):
            return returnVal

        log.debug(f'next cell -> {(x, y)}')

        if startX == stopX:

            # vertical line, move down (increase y)
            while True:
                y += self.MINFEATURESIZE/2
                returnVal += [(x, y)]
                log.debug(f'next cell -> {(x,y)}')

                if self._xy2hCell(x, y) == self._xy2hCell(stopX, stopY):
                    break

                maxLength = abs(math.ceil(stopY - startY))
                log.debug(f'num cells {len(returnVal)} and maxlength = {abs(maxLength)}')
                assert len(returnVal) <= (maxLength) * 4

        else:

            # move according to line equation y = mx + c
            m  = (by - ay)/(bx - ax)
            c  = startY - m*startX
            log.debug(f'stop condition is {self._xy2hCell(stopX, stopY)}')

            while True:
                xmax  = (x + self.MINFEATURESIZE/2)
                ynext = m*xmax + c
                ymin  = y
                ymax  = y + self.MINFEATURESIZE/2
                log.debug(f'xmax,ymax {xmax}, {ymax}')
                log.debug(f'ynext {ynext}')

                if ynext < ymin:
                    # move up
                    y = y - self.MINFEATURESIZE/2
                    returnVal += [(x, y)]
                    log.debug(f'move up to -> {(x, y)}')

                elif ynext > ymax:
                    # move down
                    y = y + self.MINFEATURESIZE/2
                    returnVal += [(x, y)]
                    log.debug(f'move down to -> {(x, y)}')

                elif ymin < ynext < ymax:
                    # move right
                    x = x + self.MINFEATURESIZE/2
                    returnVal += [(x, y)]
                    log.debug(f'move right to -> {(x, y)}')

                elif (ynext == ymin or ynext == ymax):
                    # move diagonally if trajectory isnt on cell border
                    if stopY != startY:
                        y = y + self.MINFEATURESIZE / 2
                    x = x + self.MINFEATURESIZE/2

                    returnVal += [(x, y)]
                    log.debug(f'move diagonally to -> {(x, y)}')

                if self._xy2hCell(x, y) == self._xy2hCell(stopX, stopY):
                    break

                maxLength = abs(math.ceil(stopX - startX))+abs(math.ceil(stopY-startY))
                log.debug(f'num cells {len(returnVal)} and maxlength = {abs(maxLength)}')
                assert len(returnVal) <= (maxLength)*4


        log.debug(f'new cells {returnVal}')
        return returnVal

    def _xy2hCell(self, x, y):

        # convert x,y coordinates to cell (top left coordinate)
        xsteps = int(math.floor((x)/ (self.MINFEATURESIZE/2)))
        cx     = xsteps*(self.MINFEATURESIZE/2)
        ysteps = int(math.floor((y)/ (self.MINFEATURESIZE/2)))
        cy     = ysteps*(self.MINFEATURESIZE/2)

        return (cx, cy)

    #=== UI

    def getEvaluatedPositions(self):
        '''
        Retrieve the evaluated positions of each DotBot.
        '''
        returnVal = [
            {
                'x':         dotbot['x'],
                'y':         dotbot['y'],
            } for idx, dotbot in self.dotBotsView.items()
        ]
        return returnVal

    def _hCell2SvgRect(self,cx,cy):
        returnVal = {
            'x':        cx,
            'y':        cy,
            'width':    self.MINFEATURESIZE/2,
            'height':   self.MINFEATURESIZE/2,
        }
        return returnVal

    def getExploredCells(self):
        returnVal = {
                'cellsOpen':     [self._hCell2SvgRect(*c) for c in self.exploredCells],
                'cellsObstacle': [self._hCell2SvgRect(*c) for c in self.obstacleCells],
            }
        return returnVal


    def getView(self):
        '''
        Retrieves the approximate location of the DotBot for visualization.
        '''

        returnVal = {
            'dotbotpositions': self.getEvaluatedPositions(),
            'discomap': {"complete": False, "dots": [], "lines": []},
            'exploredCells': self.getExploredCells(),
        }
        
        return returnVal
    
    #======================== private =========================================
