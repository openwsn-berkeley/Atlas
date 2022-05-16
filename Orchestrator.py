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

        # update dotBotsView
        dotbot['x']       = newX
        dotbot['y']       = newY
        self.mapBuilder.notifBump(newX, newY)
        log.debug(f'dotbot {dotbot} is at ( {newX},{newY} ) ')

        # pick new speed and heading for dotbot
        (heading, speed)  = self._pickNewMovement(frame['source'])
        dotbot['heading'] = heading
        dotbot['speed']   = speed

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

    def getView(self):
        '''
        Retrieves the approximate location of the DotBot for visualization.
        '''

        returnVal = {
            'dotbotpositions':    self.getEvaluatedPositions(),
            'discomap':           self.mapBuilder.getMap(),
            'exploredCells':      None,
        }
        
        return returnVal
    
    #======================== private =========================================
