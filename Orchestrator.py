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
        self.dotBotsView        = dict([
            (
                i,
                {
                   'x':                initX,
                   'y':                initY,
                   'heading':          0,
                   'speed':            0,
                   'movementDuration': 0
                }
            ) for i in range(1, self.numRobots+1)
        ])

        # initial movements
        for dotBotId in range(1,self.numRobots+1):
            self._updateMovement(source=dotBotId)

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

    def _updateMovement(self, source):
        '''
        modifies the movement in dotbotsview
        '''

        dotbot       = self.dotBotsView[source]

        # update DotBot's position
        (newX, newY) = u.computeCurrentPosition(
            currentX = dotbot['x'],
            currentY = dotbot['y'],
            heading  = dotbot['heading'],
            speed    = dotbot['speed'],
            duration = dotbot['movementDuration'],
        )

        dotbot['x']       = newX
        dotbot['y']       = newY
        dotbot['heading'] = 360 * random.random()
        dotbot['speed']   = 1

        log.debug(f'dotbot {dotbot} is at ( {newX},{newY} ) ')

    def receive(self,frame):
        '''
        Notification received from a DotBot.
        '''

        assert frame['frameType'] == self.FRAMETYPE_NOTIFICATION

        dotbot       = self.dotBotsView[frame['source']]
        dotbot['movementDuration'] = frame['movementDuration']
        log.debug('dotbot {} was at ( {},{} ) '.format(dotbot, dotbot['x'], dotbot['y']))

        # update dotbot position and find new speed and heading
        self._updateMovement(frame['source'])

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
    
    def getView(self):
        '''
        Retrieves the approximate location of the DotBot for visualization.
        '''
        
        returnVal = {
            'dotbotpositions':    self.getEvaluatedPositions(),
            'discomap':           None,
            'exploredCells':      None,
        }
        
        return returnVal
    
    #======================== private =========================================
