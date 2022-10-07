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

class AllRobotsAreRelays(Exception):
    pass

class Orchestrator(Wireless.WirelessDevice):
    '''
    The central orchestrator of the expedition.
    '''
    
    COMM_DOWNSTREAM_PERIOD_S    = 0.5
    MINFEATURESIZE              = 1
    
    def __init__(self, numRobots, initX, initY, relayAlgorithm="Recovery", lowerPdrThreshold=0.7, upperPdrThreshold=0.8):

        # store params
        self.numRobots                = numRobots
        self.initX                    = initX
        self.initY                    = initY
        # algorithm used to place relays
        self.relayAlgorithm           = relayAlgorithm
        self.lowerPdrThreshold        = lowerPdrThreshold
        self.upperPdrThreshold        = upperPdrThreshold

        # local variables
        self.simEngine                = SimEngine.SimEngine()
        self.wireless                 = Wireless.Wireless()
        self.dataCollector            = DataCollector.DataCollector()
        self.cellsExplored            = []
        self.cellsObstacle            = []
        self.cellsFrontier            = []
        self.x                        = self.initX
        self.y                        = self.initY
        self.dotBotId                 = 0
        self.pdrSlidingWindowPeriod   = 7
        self.lastSlidingWindowEndTime = 0
        self.lastRelayCheckTime       = 0

        # for wireless to identify if this is a relay device or not
        self.isRelay                  = False
        # to know if A* should be used for finding alternative path
        self.bumpedOnWayToTarget      = True
        # to avoid given multiple robots same frontier as target cell
        self.assignedFrontiers        = []

        self.dotBotsView              = dict([
            (
                i,
                {
                    # current position of DotBot
                    'x':                   initX,
                    'y':                   initY,
                    # current heading and speed
                    'heading':             0,
                    'speed':               0,
                    # sequence numbers (to filter out duplicate commands and notifications)
                    'seqNumCommand':       0,
                    'seqNumNotification':  None,
                    # if DotBot is relay or not
                    'isRelay':             False,
                    # duration of movement until robot stops
                    'movementTimeout':     None,
                    # if DotBot bumped or not
                    'hasJustBumped':       False,
                    # frontier cell DotBot has been given to explore and path to it
                    'targetCell':          None,
                    # to use as starting cell when computing new movement instruction
                    'lastCellExplored':    None,
                    # [(cx1, cy1) -> (cx2, cy2) -> .... -> (cxTarget, cyTarget)]
                    'currentPath':         [],
                    # last estimated PDR from DotBot
                    'estimatedPdr':        None,
                    # an array of timestamps representing when each packet was received
                    'pdrHistory':          [],
                    # [(estimated pdr, DotBot position at time of estimation), ..] (oldest -> latest)
                    'estimatedPdrHistory': [],
                    # position DotBot should go to when/if it becomes a relay
                    'relayPosition':       None,
                }
            ) for i in range(1, self.numRobots+1)
        ])

        # initial movements
        for dotBotId in range(1, self.numRobots + 1):
            self.dotBotsView[dotBotId]['heading']         = 360*random.random()
            self.dotBotsView[dotBotId]['speed']           = 1
            self.dotBotsView[dotBotId]['movementTimeout'] = 0.5

    #======================== public ==========================================

    #=== admin
    
    def startExploration(self):
        '''
        Simulation engine hands over control to orchestrator
        '''
        
        # arm first downstream communication
        self.simEngine.schedule(
            self.simEngine.currentTime(),
            self._downstreamTimeoutCb,
        )

    #=== DotBot control

    def _updateMovements(self):

        for (dotBotId, dotBot) in self.dotBotsView.items():
            # assign target cell (destination)

            if dotBot['speed'] > 0:
                continue

            if dotBot['relayPosition']:

                # DotBot has been assigned as relay, move to relay position
                targetCell = self._xy2cell(*dotBot['relayPosition'])

                # if DotBots previous target has not been explored yet,
                # release it from pool of assigned frontiers
                if dotBot['targetCell'] in self.assignedFrontiers:
                    self.assignedFrontiers.remove(dotBot['targetCell'])

            elif (
                    ((not dotBot['targetCell']) or
                     (dotBot['targetCell'] not in self.cellsFrontier))
            ):
                # target has successfully been explored
                # assign a new target cell to DotBot
                targetCell = self._computeTargetCell(dotBotId)

            else:
                # target cell not explored yet, keep moving towards it
                targetCell = dotBot['targetCell']

            # find path to target

            if ((not targetCell) or (
                    dotBot['relayPosition'] and (dotBot['relayPosition'] == (dotBot['x'], dotBot['y'])))):
                # no target or DotBot is relay and is at it's relay position
                path = None

            elif dotBot['relayPosition'] and (self._xy2cell(dotBot['x'], dotBot['y']) == targetCell):
                # relay has reached its assigned targetCell but not the exact coordinates in that cell yet.
                # we need it to be in the exact (x, y) position assigned to assure PDR is the same there.
                path = [dotBot['relayPosition']]

            elif ((targetCell != dotBot['targetCell']) or (dotBot['hasJustBumped']) or (not dotBot['currentPath'])):
                # new target, find path to it

                if dotBot['lastCellExplored']:
                    startCell = dotBot['lastCellExplored']
                else:
                    # startCell is where dotBot would be if it reversed by half a cell size.
                    startCell    = u.computeCurrentPosition(
                        currentX = dotBot['x'],
                        currentY = dotBot['y'],
                        heading  = (dotBot['heading'] + 180) % 360,
                        speed    = 1,
                        duration = (self.MINFEATURESIZE / 4),
                    )

                    # convert coordinates to cell
                    startCell = self._xy2cell(*startCell)

                path = self._computePath(startCell, targetCell)

                # if DotBot bumped into first cell on it's path at it's corner
                # add that cell as an obstacle
                if (
                        ((dotBot['x'], dotBot['y']) in self._computeCellCorners(*startCell)) and
                        dotBot['hasJustBumped'] and
                        ((dotBot['x'], dotBot['y']) == self._xy2cell(*startCell)) and
                        (not dotBot['lastCellExplored']) and
                        dotBot['currentPath']

                ):
                    self.cellsObstacle += [dotBot['currentPath'][0]]

                log.debug(
                    'new path from {} to new target {} is {}'.format((dotBot['x'], dotBot['y']), targetCell, path))

            else:
                # DotBot hasn't bumped nor reached target, keep moving along same path given upon assigning target
                # remove cells already traversed from path
                path = dotBot['currentPath'][dotBot['currentPath'].index(self._xy2cell(dotBot['x'], dotBot['y'])) + 1:]

                log.debug(
                    'same path from {} to same target {} is {}'.format((dotBot['x'], dotBot['y']), targetCell, path))

            # set new speed and heading and movementTimeout for DotBot
            if path:
                # if a DotBot is a relay and is moving to it's relay position, move it to the exact coordinates given.
                # otherwise move it to random position in cell its heading to.
                (heading, speed, movementTimeout) = self._computeHeadingSpeedMovementTimeout(
                    dotBotId                   = dotBotId,
                    path                       = path,
                    moveToRandomPositionInCell = False if (dotBot['relayPosition'] and (
                                targetCell == self._xy2cell(dotBot['x'], dotBot['y']))) else True)
            else:
                (heading, speed, movementTimeout) = (0, 0, 0.5)

            log.debug('heading & movementTimeout for {} are {} {}'.format(dotBotId, heading, movementTimeout))

            dotBot['targetCell']      = targetCell
            dotBot['currentPath']     = path
            dotBot['heading']         = heading
            dotBot['speed']           = speed
            dotBot['movementTimeout'] = movementTimeout

            # update sequence number of movement instruction
            dotBot['seqNumCommand'] += 1

            # update pdr history if using Recovery algorithm otherwise not needed
            if ((self.relayAlgorithm == "Recovery") and dotBot['estimatedPdr']):
                dotBot['estimatedPdrHistory'] += [(dotBot['estimatedPdr'], (dotBot['x'], dotBot['y']))]

    def _dotBotControl(self):
        self._computeEstimatedPdrsCb()
        self._assignRelaysAndRelayPositionsCb()
        self._updateMovements()

    #=== communication

    def _downstreamTimeoutCb(self):

        self._dotBotControl()

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
                    dotBotId,
                    {
                        'heading':         dotBot['heading'],
                        'speed':           dotBot['speed'],
                        'seqNumCommand':   dotBot['seqNumCommand'],
                        'isRelay':         dotBot['isRelay'],
                        'movementTimeout': dotBot['movementTimeout'],
                    }
                ) for (dotBotId, dotBot) in self.dotBotsView.items()]
            )
        }

        # hand over to wireless
        self.wireless.transmit(
            frame  = frameToTx,
            sender = self,
        )

        # collect PDRs
        self.dataCollector.collect(
            {
                'type':        'KPI',
                'PDRs':        self.wireless.getCurrentPDRs(),
                'numOfRelays': len([db for (_, db) in self.dotBotsView.items() if db['isRelay'] == True ]),
                'time':        self.simEngine.currentTime()
            },
        )

    def computeCurrentPosition(self):
        return (self.x, self.y)

    def receive(self,frame):
        '''
        Notification received from a DotBot, indicating it has just bumped
        '''
        assert frame['frameType'] == self.FRAMETYPE_NOTIFICATION

        # shorthand
        dotBot                         = self.dotBotsView[frame['source']]

        log.debug('DotBot {} was moving from {} to {} '.format(
            frame['source'], (dotBot['x'], dotBot['y']), dotBot['targetCell'])
        )

        # Do not compute new movements for pdr heartbeat notifications
        if frame['notificationType'] == "heartbeat":
            dotBot['pdrHistory']   += [self.simEngine.currentTime()]
            return

        # filter out duplicates
        if frame['seqNumNotification'] == dotBot['seqNumNotification']:
            return

        dotBot['seqNumNotification']   = frame['seqNumNotification']

        # update DotBot's position
        (newX, newY) = u.computeCurrentPosition(
            currentX = dotBot['x'],
            currentY = dotBot['y'],
            heading  = dotBot['heading'],
            speed    = dotBot['speed'],
            duration = frame['movementDuration'],
        )

        # update current DotBot speed stored
        dotBot['speed']                = 0

        # update explored cells
        cellsExploredAndNextCell       = self._computeCellsExploredAndNextCell(dotBot['x'], dotBot['y'], newX, newY)

        # shorthands
        cellsExplored                  = cellsExploredAndNextCell['cellsExplored']
        nextCell                       = cellsExploredAndNextCell['nextCell']

        # to determine starting cell later on when updating movement
        if cellsExplored:
            dotBot['lastCellExplored'] = cellsExplored[-1]
        else:
            dotBot['lastCellExplored'] = None

        self.cellsExplored            += cellsExploredAndNextCell['cellsExplored']

        # update obstacle cells
        if frame['hasJustBumped']:
            if nextCell:
                self.cellsObstacle += [nextCell]

            else:
                # DotBot bumped into target at corner
                if (
                    dotBot['currentPath'] == [dotBot['targetCell']]                    and
                    ((newX, newY) in self._computeCellCorners(*dotBot['targetCell']))  and
                    not cellsExplored
                ):
                    self.cellsObstacle += [dotBot['targetCell']]

        # remove explored frontiers
        self.cellsFrontier  = [
            cell for cell in self.cellsFrontier
            if (cell not in self.cellsExplored and
                cell not in self.cellsObstacle)
        ]

        # remove any corner frontiers
        for cell in self.cellsFrontier:
            self._isCornerFrontier(cell)

        # compute new frontiers
        for (cx, cy) in cellsExplored:
            for n in self._computeCellNeighbours(cx, cy):
                if (
                    (n not in self.cellsExplored) and
                    (n not in self.cellsObstacle) and
                    self._isCornerFrontier(n) == False  # check that cell isn't a corner frontier
                ):
                    self.cellsFrontier += [n]

        # remove duplicate cells while maintaining order of cells for reproducibility
        self.cellsObstacle = list(dict.fromkeys(self.cellsObstacle))
        self.cellsExplored = list(dict.fromkeys(self.cellsExplored))
        self.cellsFrontier = list(dict.fromkeys(self.cellsFrontier))

        # simulation complete when there are no more frontier cells left
        if not self.cellsFrontier:
            self.simEngine.completeRun()

        # simulation fails if all DotBots become relays
        if len([dotBot for (_,dotBot) in self.dotBotsView.items() if dotBot['isRelay'] is True]) == len(self.dotBotsView):
            raise AllRobotsAreRelays

        # update DotBotsView
        dotBot['x']      = newX
        dotBot['y']      = newY

        # store if DotBot bumped or not
        dotBot['hasJustBumped'] = frame['hasJustBumped']

    #=== Map

    def _computeCellsExploredAndNextCell(self, startX, startY, stopX, stopY):
        '''
        find cells passed through on trajectory between points a and b
        example input - output :
            {
            'in': {
                'startX': 1.10,
                'startY': 1.20,
                'stopX':  2.20,
                'stopY':  1.01,
            },
            'out': {
                'cellsExplored': [(1.00,1.00), (1.50, 1.00), (2.00, 1.00)],
                 nextCell: (2.50, 1.00)
            }
        }
        '''

        returnVal = {'cellsExplored': [], 'nextCell': None}

        # find current cell coordinates
        (cx, cy) = self._xy2cell(startX, startY)

        # check if current cell is start cell
        if startX == cx or startY == cy:
            if (stopX < startX) and (startX == cx):
                cx = cx - (self.MINFEATURESIZE / 2)
            if (stopY < startY) and (startY == cy):
                cy = cy - (self.MINFEATURESIZE / 2)

        log.debug(f'find cells explored: start at {(startX, startY)} stop at {(stopX, stopY)}')
        # maxNumCells is length of line *2 as each cell is 1/2 the size of a unit step
        # we add an extra 2 cells: 1 - in case start cell is not the initial cell and
        # 1 - for when we calculate the next cell beyond the trajectory
        maxNumCells = u.distance((startX, startY), (stopX, stopY)) * 2 + 2

        # movement is not on boundaries
        if not (
                ((startX == stopX) and ((startX == cx) or (startX == (cx + self.MINFEATURESIZE / 2)))) or
                ((startY == stopY) and ((startY == cy) or (startY == (cy + self.MINFEATURESIZE / 2))))
        ):
            returnVal['cellsExplored'] += [(cx, cy)]
            cellsExploredComputed       = False

            if startX == stopX:

                # vertical line, move up or down
                while cellsExploredComputed == False:
                    xmax = cx + self.MINFEATURESIZE / 2
                    ymax = cy + self.MINFEATURESIZE / 2

                    if (
                            cx <= stopX <= xmax and
                            cy <= stopY <= ymax
                    ):
                        cellsExploredComputed = True

                    if startY < stopY:
                        cy = cy + self.MINFEATURESIZE / 2
                    else:
                        cy = cy - self.MINFEATURESIZE / 2
                    returnVal['cellsExplored'] += [(cx, cy)]

                    assert len(returnVal) <= maxNumCells

            else:

                # move according to line equation y = mx + c
                m = (stopY - startY) / (stopX - startX)
                c = startY - m * startX

                while cellsExploredComputed == False:

                    ymin = cy
                    ymax = cy + (self.MINFEATURESIZE / 2)
                    xmax = cx + (self.MINFEATURESIZE / 2)

                    if startX < stopX:
                        # movement towards right side
                        ynext = m * xmax + c
                        slope = 1
                    else:
                        # movement towards left side
                        ynext = m * cx + c
                        slope = -1

                    # round
                    ynext = round(ynext, 9)

                    if (
                            cx <= stopX <= xmax and
                            cy <= stopY <= ymax
                    ):
                        cellsExploredComputed = True

                    if ynext < ymin:
                        # move up
                        cy = cy - (self.MINFEATURESIZE / 2)
                        returnVal['cellsExplored'] += [(cx, cy)]

                    elif ymax < ynext:
                        # move down
                        cy = cy + (self.MINFEATURESIZE / 2)
                        returnVal['cellsExplored'] += [(cx, cy)]

                    elif ynext == ymin:
                        # move diagonally upwards
                        cx = cx + (self.MINFEATURESIZE / 2) * slope
                        cy = cy - (self.MINFEATURESIZE / 2)
                        returnVal['cellsExplored'] += [(cx, cy)]

                    elif ynext == ymax:
                        # move diagonally downwards
                        cx = cx + (self.MINFEATURESIZE / 2) * slope
                        cy = cy + (self.MINFEATURESIZE / 2)
                        returnVal['cellsExplored'] += [(cx, cy)]

                    else:
                        # move sideways
                        cx = cx + (self.MINFEATURESIZE / 2) * slope
                        returnVal['cellsExplored'] += [(cx, cy)]

                    assert len(returnVal) <= maxNumCells

            returnVal['nextCell'] = returnVal['cellsExplored'].pop(-1)

            # if stop coordinates are exactly on a corner (connecting 4 cells), next cell is not certain
            if (stopX, stopY) in self._computeCellCorners(stopX, stopY):
                returnVal['nextCell'] = None
        log.debug(f'cells explored {returnVal}')
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
                'isRelay':   dotBot['isRelay'],
            } for dotBotId, dotBot in self.dotBotsView.items()
        ]
        return returnVal

    def getView(self):
        '''
        Retrieves the approximate location of the DotBot for visualization.
        '''

        returnVal = {
            'dotBotpositions':  self.getEvaluatedPositions(),
            'cellsExplored':   [self._cell2SvgRect(*c) for c in self.cellsExplored],
            'cellsObstacle':   [self._cell2SvgRect(*c) for c in self.cellsObstacle],
            'cellsFrontier':   [self._cell2SvgRect(*c) for c in self.cellsFrontier],
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
        cellSize  = self.MINFEATURESIZE/2

        returnVal = [
            (cx+cellSize, cy),          (cx-cellSize, cy),
            (cx,          cy-cellSize), (cx,          cy+cellSize),
            (cx-cellSize, cy-cellSize), (cx+cellSize, cy+cellSize),
            (cx-cellSize, cy+cellSize), (cx+cellSize, cy-cellSize)
        ]

        return returnVal

    def _computeCellCorners(self, x, y):

        (cxmin, cymin)    = self._xy2cell(x, y)
        (cxmax, cymax)    = (cxmin + self.MINFEATURESIZE/2, cymin + self.MINFEATURESIZE/2)

        topLeftCorner     = (cxmin, cymin)
        topRightCorner    = (cxmax, cymin)
        bottomLeftCorner  = (cxmin, cymax)
        bottomRightCorner = (cxmax, cymax)

        return [topLeftCorner, topRightCorner, bottomLeftCorner, bottomRightCorner]

    def _isCornerFrontier(self, cell):
        '''
        evaluates if potential frontier cell is corner frontier or not.
        example input-output:
            {
            'in': {
                'cell': (0.50, 5.00)
            },
            'out': True
        },
        '''

        returnVal          = False
        neighbourObstacles = []

        # check for obstacle in 1-hop neighbourhood of frontier
        for n in self._computeCellNeighbours(*cell):
            if n in self.cellsObstacle:
                neighbourObstacles += [n]

        # find all diagonal obstacles connected to frontier
        for (cx, cy) in neighbourObstacles:

            # check for second obstacle diagonal to the first one
            for (nx, ny) in self._computeCellNeighbours(*cell):

                if (nx, ny) == cell:
                    # this obstacle is the first obstacle
                    continue

                if (nx, ny) not in self.cellsObstacle or nx == cx or ny == cy:
                    # cell not diagonal obstacle to first obstacle detected
                    # skip this cell
                    continue

                # if reached here, 2 diagonal obstacles have been detected
                # find corner where obstacles connect diagonally (common corner)
                firstObstacleCorners  = set(self._computeCellCorners(cx, cy))
                secondObstacleCorners = set(self._computeCellCorners(nx, ny))

                commonCorner          = firstObstacleCorners.intersection(secondObstacleCorners)

                if not commonCorner:
                    continue

                (ccx, ccy)     = list(commonCorner)[0]

                cellSize       = self.MINFEATURESIZE / 2
                connectedCells = [
                    (ccx - cellSize, ccy - cellSize),
                    (ccx, ccy - cellSize),
                    (ccx, ccy),
                    (ccx - cellSize, ccy)
                ]

                # check that there is one explored cell connected to diagonal obstacles and frontier
                # at same connecting corner
                for c in connectedCells:
                    if c in self.cellsExplored:
                        # remove cell from frontiers if it is already set as one
                        if cell in self.cellsFrontier:
                            self.cellsFrontier.remove(cell)
                        returnVal = True
                        break

        return returnVal

    # === Exploration

    def _computeTargetCell(self, dotBotId):
        dotBot         = self.dotBotsView[dotBotId]
        targetFrontier =  None

        self.assignedFrontiers = [frontier for frontier in self.assignedFrontiers if frontier in self.cellsFrontier]

        if len(self.cellsFrontier) == len(self.assignedFrontiers):
            # if all frontiers are assigned to DotBots, clear assigned frontiers, to avoid frontier cells not
            # being explored if the DotBot they are assigned to has lost connectivity.
            self.assignedFrontiers = []

        if self.cellsFrontier:
            targetFrontiers = [((cx, cy), u.distance((dotBot['x'], dotBot['y']), (cx, cy))) for (cx, cy) in
                                              self.cellsFrontier if (cx, cy) not in self.assignedFrontiers]
            targetFrontier  = sorted(targetFrontiers, key=lambda e: e[1])[0][0]

            self.assignedFrontiers += [targetFrontier]

        return targetFrontier

    # === Navigation

    def _computePath(self, startCell, targetCell):
        """
        uses A* (Breadth First Search with distance to target heuristic) to find
        shortest path from start to target cell while avoiding obstacle cells.
        if robot is on obstacle between cells, diagonal cells can be excluded
        from the search to avoid trying to move through unexplored obstacle cells.
        Example input - output:
            {
        'in': {
            'startCell':             (0.00, 0.00),
            'targetCell':            (2.00, 2.00),
            'excludeDiagonalCells' : False
        },
        'out': {
            'path': [
                (0.50, 0.50),
                (1.00, 1.00),
                (1.50, 1.50),
                (2.00, 2.00)
            ],
        },
    },
        """

        openCells   = []
        openCells  += [u.AstarNode(startCell, parent=None)]
        closedCells = []
        path        = []

        while openCells:

            # find open cell with lowest F cost
            currentCell = min(openCells)
            openCells.remove(currentCell)

            if currentCell is None:
                log.warning("NO PATH!")
                return

            closedCells += [currentCell]

            # backtrack direct path if we have reached target

            if currentCell.cellPos == targetCell:

                path = []

                while currentCell.cellPos != startCell:
                    path       += [currentCell.cellPos]
                    currentCell = currentCell.parent

                path.reverse()
                break

            cellNeighbours = self._computeCellNeighbours(*currentCell.cellPos)

            (cx, cy)       = currentCell.cellPos
            cellSize       = self.MINFEATURESIZE / 2
            diagonalCells  = [
                (cx - cellSize, cy - cellSize), (cx + cellSize, cy - cellSize),
                (cx - cellSize, cy + cellSize), (cx + cellSize, cy + cellSize),
            ]

            for childCell in cellNeighbours:
                childCell      = u.AstarNode(childCell, currentCell)
                gCost          = currentCell.gCost + 1

                # skip cells that have not been explored
                if childCell.cellPos not in self.cellsFrontier and childCell.cellPos not in self.cellsExplored:
                    continue

                # add extra cost to frontier cells (if they are diagonal and are not the target)
                # to prioritise explored cells over frontiers and to avoid building paths through undiscovered obstacles
                if childCell.cellPos in self.cellsFrontier and childCell.cellPos in diagonalCells and childCell.cellPos != targetCell:
                    addedCost  = 10
                    log.debug(f'adding cost to diagonal cell {childCell.cellPos}')
                else:
                    addedCost  = 0
                hCost          = u.distance(childCell.cellPos, targetCell) + addedCost

                # skip cell if it is an obstacle cell
                if childCell.cellPos in self.cellsObstacle:
                    continue

                # skip cell if it is diagonal to current/parent cell and is connected to an obstacle cell
                # that parent cell is connected to to avoid moving to cell through corners
                if childCell.cellPos in diagonalCells:
                    obstacleNeighboursOfChild = [
                        cell for cell in self._computeCellNeighbours(*childCell.cellPos) if cell in self.cellsObstacle
                    ]

                    obstacleNeighboursOfParent = [
                        cell for cell in self._computeCellNeighbours(*childCell.cellPos) if cell in self.cellsObstacle
                    ]

                    if set(obstacleNeighboursOfChild).intersection(set(obstacleNeighboursOfParent)):
                       continue

                if (
                    (childCell.cellPos in [cell.cellPos for cell in openCells] or
                     childCell.cellPos in [cell.cellPos for cell in closedCells]) and
                    (childCell.fCost <= gCost + hCost)
                ):
                    continue

                childCell.gCost = gCost
                childCell.hCost = hCost
                childCell.fCost = gCost + hCost

                openCells += [childCell]

        log.debug(f'A* path from {startCell} to {targetCell} is {path}')
        log.debug(f'frontier cells in path are {[c for c in path if c in self.cellsFrontier]}')
        return path

    def _computeHeadingSpeedMovementTimeout(self, dotBotId, path, moveToRandomPositionInCell=True):

        dotBot         = self.dotBotsView[dotBotId]

        # shift coordinates from cell center to compute movement to random position in cell
        # otherwise compute movement to exact target coordinates given.
        shift          = random.uniform(0.01, ((self.MINFEATURESIZE/2) - 0.01)) if moveToRandomPositionInCell is True else 0

        # find initial heading and distance to reach first cell in path (to use as reference)
        initialHeading = (math.degrees(math.atan2(path[0][1] - dotBot['y'], path[0][0] - dotBot['x'])) + 90) % 360

        # destination center coordinates of target (if no obstacles on path) or of last cell before changing heading
        # movement is from cell centre to cell centre to avoid movements across cell borders and assure
        # passing though cells to explore them
        destination    = (path[0][0] + shift, path[0][1] + shift)

        # compute distance DotBot will move along same trajectory until heading changes from initial one
        for idx, (cx, cy) in enumerate(path):

            if (cx, cy) == path[-1]:
                # target is the only cell in the path
                break

            # find heading to center of next cell
            headingToNext = (math.degrees(math.atan2(path[idx + 1][1] - cy, path[idx + 1][0] - cx)) + 90) % 360

            if headingToNext != initialHeading:
                # heading changes
                destination   = (cx + shift, cy + shift)
                break

        # find distance to destination cell from DotBot position
        distance = u.distance((dotBot['x'], dotBot['y']), destination)

        # heading to get to destination cell center (to assure exploration and avoid border to border movement)
        heading = (
            math.degrees(math.atan2(destination[1] - dotBot['y'], destination[0] - dotBot['x'])) + 90
                  ) % 360

        # set speed
        speed   = 1

        # find movementTimeout to stop at target cell
        movementTimeout = distance / speed

        log.debug('[computeHeadingSpeedMovementTimeout] moving from  {} to {}, heading {}, time {}'.format(
            (dotBot['x'], dotBot['y']),
            destination, heading,
            movementTimeout)
        )

        return (heading, speed, movementTimeout)

    # === Relays

    def _computeEstimatedPdrsCb(self):

        if (self.simEngine.currentTime() - self.lastSlidingWindowEndTime) < self.pdrSlidingWindowPeriod:
            return

        for ( _, dotBot) in self.dotBotsView.items():
            numOfPackerRxed        = 0
            slidingWindowStartTime = self.lastSlidingWindowEndTime
            slidingWindowEndTime   = slidingWindowStartTime + self.pdrSlidingWindowPeriod
            dotBot['pdrHistory']   = [time for time in dotBot['pdrHistory'] if time >= slidingWindowStartTime]

            for time in dotBot['pdrHistory']:

                if time >= slidingWindowEndTime:
                    break

                numOfPackerRxed += 1

            # FIXME: *2 should be change to variable/relationship to
            dotBot['estimatedPdr'] = (numOfPackerRxed/((self.pdrSlidingWindowPeriod)*2))
            logging.debug('estimated pdr for dotbot {} is {} '.format(_,dotBot['estimatedPdr']))
            assert  0 <= dotBot['estimatedPdr'] <= 1

        self.lastSlidingWindowEndTime = slidingWindowEndTime


    def _assignRelaysAndRelayPositionsCb(self):

        log.debug('estimated PDRs {}'.format([db['estimatedPdr'] for (_, db) in self.dotBotsView.items()]))

        if self.relayAlgorithm   == "Recovery":
            self._relayPlacementRecovery()

        elif self.relayAlgorithm == "SelfHealing":
            self._relayPlacementSelfHealing()

        else:
            # don't place relays if no algorithm is specified
            pass

    def _relayPlacementRecovery(self):

        LOWER_PDR_THRESHOLD = self.lowerPdrThreshold
        UPPER_PDR_THRESHOLD = self.upperPdrThreshold

        # only check for need for relays if estimated PDRs have been updated
        if ((self.simEngine.currentTime() - self.lastRelayCheckTime) < self.pdrSlidingWindowPeriod):
            return

        self.lastRelayCheckTime = self.simEngine.currentTime()

        # find DotBots that have an average PDR (over a defined time window) that is <= lower PDR threshold
        dotBotsWithAvgPdrBelowThreshold = [
            (db, db['estimatedPdr']) for (_, db) in self.dotBotsView.items() if
            (db['estimatedPdrHistory'] and
            ((db['estimatedPdr'] <= LOWER_PDR_THRESHOLD) and
            (not db['isRelay'])))
        ]

        if not dotBotsWithAvgPdrBelowThreshold:
            return

        # out of all DotBots with PDRs falling below lower threshold, select one with highest PDR to become relay
        # to assure communication between Orchestrator and relay DotBot until DotBot reaches it's relay position.
        dotBotToBecomeRelay              = sorted(dotBotsWithAvgPdrBelowThreshold, key=lambda e: e[1])[-1][0]

        # assign DotBot as relay
        dotBotToBecomeRelay['isRelay']   = True

        # get stored PDR history (oldest -> latest)
        estimatedPdrHistory              = dotBotToBecomeRelay['estimatedPdrHistory']

        # reverse PDR history (latest -> oldest)
        pdrHistoryReversed               = estimatedPdrHistory[::-1]

        for (pdrValue, (dotBotX, dotBotY)) in pdrHistoryReversed:

            # look for last DotBot position with PDR above upper threshold
            if pdrValue >= UPPER_PDR_THRESHOLD:
                if (self._xy2cell(dotBotX, dotBotY) in self.cellsExplored):
                    # set relay position for DotBot to move to
                    dotBotToBecomeRelay['relayPosition']     = (dotBotX, dotBotY)
                    break


    def _relayPlacementSelfHealing(self):

        RANGE_DISTANCE = 7  # up to 10m pister-hack stability minimum PDR is still above 0

        # check if orchestrator has lost connection to any DotBots
        for (dotBotId, dotBot) in self.dotBotsView.items():

            lostDotBot = dotBot

            # find distance between lostDotBot and orchestrator
            startToLostDotBotDistance           = [
                ((self.x, self.y) ,u.distance((lostDotBot['x'], lostDotBot['y']), (self.x, self.y)))
            ]

            # find all relay positions
            relayPositions                      = [
                dotBot['relayPosition'] for (_, dotBot) in self.dotBotsView.items() if dotBot['relayPosition']
            ]

            # if we already have relays in place, build relay chain starting from closest relay to
            # lostDotBot instead of orchestrator

            relaysToLostDotBotDistances         = [
                (position, u.distance((lostDotBot['x'], lostDotBot['y']), position)) for position in relayPositions
            ]

            closestRelayToLostDotBotAndDistance = sorted(
                startToLostDotBotDistance + relaysToLostDotBotDistances, key=lambda e: e[1]
            )[0]

            rootRelay                           = closestRelayToLostDotBotAndDistance[0]
            rootRelayToLostDotBotDistance       = closestRelayToLostDotBotAndDistance[1]
            distancesRatio                      = RANGE_DISTANCE / rootRelayToLostDotBotDistance
            numRelays                           = int(rootRelayToLostDotBotDistance / RANGE_DISTANCE)

            if numRelays == 0:
                continue

            # equations bellow from https://math.stackexchange.com/a/1630886

            # build relay chain to restore connectivity to lostDotBot
            previousRelayInChain = rootRelay
            for idx in range(numRelays):
                (x0, y0) = previousRelayInChain
                (x1, y1) = (lostDotBot['x'], lostDotBot['y'])

                nextPosInChain       = (
                    int(((1 - distancesRatio) * x0 + distancesRatio * x1)),
                    int(((1 - distancesRatio) * y0 + distancesRatio * y1))
                )

                # chose random DotBot to be relay
                try:
                    dotBot               = random.choice(
                        [
                            db for (id, db) in self.dotBotsView.items() if
                            (db != lostDotBot and ((db['x'], db['y']) and (not db['relayPosition']) and (db != lostDotBot)))
                        ]
                    )
                except IndexError:
                    # no valid DotBots left to be placed as relays
                    return

                # set DotBot as relay
                dotBot['isRelay'] = True

                if (
                   (self._xy2cell(*nextPosInChain) in     self.cellsExplored)  and
                   (self._xy2cell(*nextPosInChain) not in self.cellsObstacle)
                ):
                    # next position in chain is valid set it as relay position
                    dotBot['relayPosition'] = nextPosInChain
                else:
                    # next position in relay chain is not an explored cell/valid
                    # keep searching around in until an explored cell is found
                    # to replace it

                    open_cells   = [self._xy2cell(*nextPosInChain)]
                    closed_cells = []

                    for cell in open_cells:
                        open_cells.pop(0)
                        for n in self._computeCellNeighbours(*cell):
                            if (n in self.cellsExplored) and (n not in self.cellsObstacle):
                                dotBot['relayPosition'] = n
                                break

                            if n not in closed_cells and n not in open_cells:
                                open_cells.append(n)

                        closed_cells.append(cell)

                        if dotBot['relayPosition']:
                            break

                # move on to next relay in chain
                previousRelayInChain = nextPosInChain
