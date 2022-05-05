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
                   'x':       initX,
                   'y':       initY,
                   'heading': 0,
                   'speed':   0,
                }
            ) for i in range(1,self.numRobots+1)
        ])

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

        frameToTx = {
            'frameType': self.FRAMETYPE_COMMAND,
            'movements': dict([
                    (
                        idx,
                        {
                           'heading': 360 * random.random(),
                           'speed':   1,
                        }
                    ) for idx, dotbot in self.dotBotsView.items()]
            )
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
        assert frame['frameType'] == self.FRAMETYPE_NOTIFICATION
        dotbot       = self.dotBotsView[frame['source']]
        log.debug('dotbot {} was at ( {},{} ) '.format(dotbot, dotbot['x'], dotbot['y']))

        # update DotBot's position
        (newX,newY)  = u.computeCurrentPosition(
            currentX = dotbot['x'],
            currentY = dotbot['y'],
            heading  = dotbot['heading'],
            speed    = dotbot['speed'],
            duration = frame['duration'],
        )

        dotbot['x']  = newX
        dotbot['y']  = newY
        log.debug(f'dotbot {dotbot} is at ( {newX},{newY} ) ')

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
            'width':    1/2,
            'height':   1/2,
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
