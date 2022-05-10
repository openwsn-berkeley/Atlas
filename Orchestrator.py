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
        self.hCellsOpen         = [(self.initX, self.initY)]
        self.hCellsObstacle     = []
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
        self.hCellsObstacle += [self._xy2hCell(newX, newY)]
        cellsTraversed       = self._cellsTraversed(dotbot['x'], dotbot['y'], newX, newY)
        self.hCellsOpen     += [c for c in cellsTraversed if c not in self.hCellsObstacle]

        # if a cell is obstacle, remove from open cells
        try:
            self.hCellsOpen.remove(self._xy2hCell(newX, newY))
        except ValueError:
            pass

        # remove duplicate cells
        self.hCellsObstacle  = list(set(self.hCellsObstacle))
        self.hCellsOpen      = list(set(self.hCellsOpen))

        # update dotBotsView
        dotbot['x']       = newX
        dotbot['y']       = newY

        # pick new speed and heading for dotbot
        (heading, speed) = self._pickNewMovement(frame['source'])
        dotbot['heading'] = heading
        dotbot['speed']   = speed

    #=== Map

    def _cellsTraversed(self, ax, ay, bx, by):
        '''
        find cells on trajectory between points a and b
        '''
        # FIXME: add cases where startX = StopX and y in negative direction
        # shorthand
        cellSize  = self.MINFEATURESIZE/2

        # dotbot hasn't moved
        if ax == bx and ay == by:
            return []

        # set starting point as one with smallest x
        # x should always move in a positive direction
        if ax < bx or ax == bx:
            (startX, startY) = (ax, ay)
            (stopX,  stopY)  = (bx, by)
            (minX,   maxX)   = (ax, bx)
            xDirection       =  1
        else:
            (startX, startY) = (bx, by)
            (stopX,  stopY)  = (ax, ay)
            (minX,   maxX)   = (bx, ax)
            xDirection       =  -1       # refers to original direction of movement

        # check direction of y axis movement
        if stopY < startY:
            (minY, maxY) = (stopY,startY)
            yDirection   = -1
        else:
            (minY, maxY) = (startY, stopY)
            yDirection   = 1

        # find the distance of movement from cell to cell
        stepX   =  cellSize
        stepY   =  cellSize * yDirection

        # find the distance of movement from cell to cell with direction
        tDeltaX = (cellSize / (stopX - startX)) if startX != stopX else 0
        tDeltaY = (cellSize / (stopY - startY)) if startY != stopY else 0

        # find starting cell from starting point
        if xDirection == 1 and yDirection == -1:
            (indexX, indexY) = (stopX, stopY)
        else:
            (indexX, indexY) = (startX, startY)

        (currentXindex, currentYindex) = self._xy2hCell(indexX,indexY)
        log.debug(f'starting at point ({startX}, {startY}) in cell ({currentXindex}, {currentYindex})')

        # find first distance till next intersection with an axis
        # the tDelta values are added to this value to move across the trajectory from cell to cell
        txMax = (currentXindex - startX) / (stopX - startX) if startX != stopX else math.inf
        tyMax = (currentYindex - startY) / (stopY - startY) if startY != stopY else math.inf
        log.debug(f'tmaxx,tmaxy : {txMax}, {tyMax}')

        # loop to shift across trajectory and find all cells
        (x, y) = (startX, startY)
        returnVal = []
        while True:
            log.debug(f'previous cell : {self._xy2hCell(x,y)}')
            if (txMax < tyMax):
                x = x + stepX
                if x > maxX or x < minX:
                    break
                txMax = txMax + tDeltaX
                returnVal += [self._xy2hCell(x, y)]
            else:
                y = y + stepY
                if y > maxY or y < minY:
                    break
                tyMax = tyMax + tDeltaY*yDirection
                returnVal += [self._xy2hCell(x, y)]

            log.debug(f'next point : {x},{y}')
            log.debug(f'next cell  : {self._xy2hCell(x, y)}')

        # filter duplicates
        returnVal = list(set(returnVal))
        log.debug(f'new cells found -> {returnVal}')
        return returnVal

    def _xy2hCell(self, x, y):
        if (x - math.floor(x)) <  (self.MINFEATURESIZE/2):
            cx = math.floor(x) + (self.MINFEATURESIZE/2)
        elif (x - math.floor(x)) >  (self.MINFEATURESIZE/2):
            cx = math.floor(x) + self.MINFEATURESIZE
        else:
            cx = x

        if (y - math.floor(y)) <  (self.MINFEATURESIZE/2) and (y - math.floor(y)) > 0:
            cy = math.floor(y) + (self.MINFEATURESIZE/2)
        elif (y - math.floor(y)) >  (self.MINFEATURESIZE/2) and (y - math.floor(y)) > 0:
            cy = math.floor(y) + self.MINFEATURESIZE
        else:
            cy = y

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
            'x':        cx-self.MINFEATURESIZE/2,
            'y':        cy-self.MINFEATURESIZE/2,
            'width':    self.MINFEATURESIZE/2,
            'height':   self.MINFEATURESIZE/2,
        }
        return returnVal

    def getExploredCells(self):
        returnVal = {
                'cellsOpen':     [self._hCell2SvgRect(*c) for c in self.hCellsOpen],
                'cellsObstacle': [self._hCell2SvgRect(*c) for c in self.hCellsObstacle],
            }
        return returnVal

    def getView(self):
        '''
        Retrieves the approximate location of the DotBot for visualization.
        '''

        returnVal = {
            'dotbotpositions':    self.getEvaluatedPositions(),
            'discomap':           {"complete": False, "dots": [], "lines": []},
            'exploredCells':      self.getExploredCells(),
        }
        
        return returnVal
    
    #======================== private =========================================
