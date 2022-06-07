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
                    # current position of dotBot
                   'x':                  initX,
                   'y':                  initY,
                    # current heading and speed
                   'heading':            0,
                   'speed':              0,
                    # sequence numbers (to filter out duplicate commands and notifications)
                   'seqNumCommand':      0,
                   'seqNumNotification': None,
                    # if dotBot is relay or not
                   'isRelay':            False,
                    # duration of movement until robot stops
                   'timeout':            None,
                    # if dotBot bumped last time it stopped
                    'bumped':            False,
                    # frontier cell dotBot has been given to explore and path to it
                    'targetCell':        None,
                    'currentPath':       [],
                }
            ) for i in range(1, self.numRobots+1)
        ])

        # initial movements
        for dotBotId in range(1,self.numRobots+1):
            (heading, speed, timeout)             = self._computeHeadingSpeedTimeout(path=[], dotBotId=dotBotId)
            self.dotBotsView[dotBotId]['heading'] = heading
            self.dotBotsView[dotBotId]['speed']   = speed
            self.dotBotsView[dotBotId]['timeout'] = timeout

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
                        'heading':        dotBot['heading'],
                        'speed':          dotBot['speed'],
                        'seqNumCommand':  dotBot['seqNumCommand'],
                        'isRelay':        dotBot['isRelay'],
                        'timeout':        dotBot['timeout'],
                    }
                ) for (dotBotId, dotBot) in self.dotBotsView.items()]
            )
        }

        # hand over to wireless
        self.wireless.transmit(
            frame  = frameToTx,
            sender = self,
        )

    def receive(self,frame):
        '''
        Notification received from a DotBot, indicating it has just bumped
        '''

        assert frame['frameType'] == self.FRAMETYPE_NOTIFICATION

        # shorthand
        dotBot       = self.dotBotsView[frame['source']]

        # filter out duplicates
        if frame['seqNumNotification'] == dotBot['seqNumNotification']:
            return
        dotBot['seqNumNotification'] = frame['seqNumNotification']

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

        # update obstacle cells if dotBot has bumped
        if cellsExplored['nextCell'] and frame['bumped']:
            self.cellsObstacle  += [cellsExplored['nextCell']]

        # remove explored frontiers
        self.cellsFrontier = [
            cell for cell in self.cellsFrontier
            if (cell not in self.cellsExplored and
                cell not in self.cellsObstacle)
        ]

        # compute new frontiers
        for (cx, cy) in cellsExplored['cellsExplored']:
            for n in self._computeCellNeighbours(cx, cy):
                if (
                    (n not in self.cellsExplored) and
                    (n not in self.cellsObstacle) and
                    self._isCornerFrontier(n) == False     # check that cell isn't a corner frontier
                ):
                    self.cellsFrontier += [n]

        # remove duplicate cells
        self.cellsObstacle = list(set(self.cellsObstacle))
        self.cellsExplored = list(set(self.cellsExplored))
        self.cellsFrontier = list(set(self.cellsFrontier))

        # simulation complete when there are no more frontier cells left
        if not self.cellsFrontier:
            self.simEngine.completeRun()
            return

        # update dotBotsView
        dotBot['x']       = newX
        dotBot['y']       = newY
        dotBot['bumped']  = frame['bumped']

        assert cellsExplored['cellsExplored']

        # assign dotBot a new target if it's previous target has successfully been explored
        # otherwise continue moving towards same target.
        if not dotBot['targetCell'] or dotBot['targetCell'] not in self.cellsFrontier:

            # assign a new target cell (destination) to dotBot
            targetCell               = self._assignCellToExplore(frame['source'])

            # find shortest path to target if dotBot hasn't bumped otherwise find path with no diagonal movements
            # to avoid bumping into frontiers at frontier corners (as they wont be added as obstacles)
            path                     = self._computePathToTarget(
                startCell            = cellsExplored['cellsExplored'][-1],
                targetCell           = targetCell,
                excludeDiagonalCells = True if frame['bumped'] else False
            )
            log.debug('new path from {} to new target {} is {}'.format((newX, newY), targetCell, path))

            # store update target cell and path in dotBots view
            dotBot['currentPath']    = path
            dotBot['targetCell']     = targetCell

        else:

            # continue going towards same target cell
            targetCell               = dotBot['targetCell']

            if frame['bumped']:
                # dotBot bumped on way to target

                # find a new path around obstacle (no diagonal cells)
                path                     = self._computePathToTarget(
                    startCell            = cellsExplored['cellsExplored'][-1],
                    targetCell           = targetCell,
                    excludeDiagonalCells = True
                )
                log.debug('new path from {} to same target {} is {}'.format((newX, newY), targetCell, path))

                # update path in dotbots view
                dotBot['currentPath'] = path

            else:
                # dotBot hasn't bumped nor reached target, keep moving along same path given upon assigning target
                # remove cells already traversed from path
                path                  = dotBot['currentPath'][dotBot['currentPath'].index(self._xy2cell(newX, newY))+1:]

                # update path in dotbots view
                dotBot['currentPath'] = path

                log.debug('same path from {} to same target {} is {}'.format((newX, newY), targetCell, path))

        # set new speed and heading and timeout for dotBot
        (heading, speed, timeout) = self._computeHeadingSpeedTimeout(path, frame['source'])
        log.debug('heading & timeout for {} are {} {}'.format(frame['source'], heading, timeout))

        dotBot['heading']         = heading
        dotBot['speed']           = speed
        dotBot['timeout']         = timeout

        # update sequence number of movement instruction
        dotBot['seqNumCommand']  += 1

        # set relay status (temporary until relay algorithms are added!!)
        dotBot['isRelay']         = True if frame['source'] in [2] else False

    def computeCurrentPosition(self):
        '''
        for wireless calculations of PDR
        '''
        return (self.initX, self.initY)

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
            'exploredCells':   {
                'cellsExplored': [self._cell2SvgRect(*c) for c in self.cellsExplored],
                'cellsObstacle': [self._cell2SvgRect(*c) for c in self.cellsObstacle],
                'cellsFrontier': [self._cell2SvgRect(*c) for c in self.cellsFrontier],
            },
        }

        return returnVal
    
    #======================== private =========================================

    #===== Map
    def _computeCellsExplored(self, startX, startY, stopX, stopY):
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

            # if stop coordinates are exactly on a corner (connecting 4 cells), next cell is not certain
            if (stopX, stopY) in self._computeCellCorners(stopX, stopY):
                returnVal['nextCell'] = None

        log.debug(f'new cells {returnVal}')


        return returnVal

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

        returnVal     = False
        firstObstacle = None

        # check for obstacle in 1-hop neighbourhood of frontier
        for n in self._computeCellNeighbours(*cell):
            if n in self.cellsObstacle:
                firstObstacle = n
                break

        if firstObstacle:

            (cx, cy) = firstObstacle

            # check for second obstacle diagonal to the first one
            for (nx, ny) in self._computeCellNeighbours(cx, cy):

                if (nx, ny) not in self.cellsObstacle or nx == cx or ny == cy:
                    # cell not diagonal obstacle to first obstacle detected
                    # skip this cell
                    continue

                # if reached here, 2 diagonal obstacles have been detected
                # find corner where obstacles connect diagonally (common corner)
                firstObstacleCorners  = set(self._computeCellCorners(cx, cy))
                secondObstacleCorners = set(self._computeCellCorners(nx, ny))

                commonCorner = firstObstacleCorners.intersection(secondObstacleCorners)
                (ccx, ccy) = list(commonCorner)[0]

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
    def _assignCellToExplore(self, dotBotId):

        dotBot = self.dotBotsView[dotBotId]

        # find closest frontiers to initial position
        cellsAndDistancesToStart  = [((cx, cy), u.distance((self.initX, self.initY), (cx, cy))) for (cx, cy) in self.cellsFrontier]
        cellsAndDistancesToStart  = sorted(cellsAndDistancesToStart, key=lambda e: e[1])
        closestFrontiersToStart   = [cell for (cell, distance) in cellsAndDistancesToStart if distance==cellsAndDistancesToStart[0][1]]

        # find closest frontier to robot
        cellsAndDistancesToDotBot  = [((cx, cy), u.distance((dotBot['x'], dotBot['y']), (cx, cy))) for (cx, cy) in closestFrontiersToStart]
        cellsAndDistancesToDotBot  = sorted(cellsAndDistancesToDotBot, key=lambda e: e[1])
        closestFrontiersToDotBot   = [cell for (cell, distance) in cellsAndDistancesToDotBot if distance==cellsAndDistancesToDotBot[0][1]]

        return random.choice(closestFrontiersToDotBot)

    # === Navigation
    def _computePathToTarget(self, startCell, targetCell, excludeDiagonalCells=False):

        openCells   = []
        openCells  += [u.AstarNode(startCell, parent=None)]
        closedCells = []
        path        = []

        while openCells:

            # find open cell with lowest F cost
            currentCell   = min(openCells)
            openCells.remove(currentCell)

            if currentCell is None:
                log.warning("NO PATH!")
                return

            closedCells += [currentCell]

            # backtrack direct path if we have reached target

            if currentCell.cellPos == targetCell:

                path     = []

                while currentCell.cellPos != startCell:

                    path       += [currentCell.cellPos]
                    currentCell = currentCell.parent

                path.reverse()
                break

            if excludeDiagonalCells:
                (cx, cy)       = currentCell.cellPos
                cellSize       = self.MINFEATURESIZE/2
                cellNeighbours = [
                    (cx+cellSize, cy),          (cx-cellSize, cy),
                    (cx,          cy-cellSize), (cx,          cy+cellSize),
                ]
            else:
                cellNeighbours = self._computeCellNeighbours(*currentCell.cellPos)

            for childCell in cellNeighbours:
                childCell = u.AstarNode(childCell, currentCell)
                gCost     = currentCell.gCost + 1
                hCost     = u.distance(childCell.cellPos, targetCell)

                # skip cell if it is an obstacle cell
                if childCell.cellPos in self.cellsObstacle:
                    continue

                if (
                    (childCell.cellPos in [cell.cellPos for cell in openCells]  or
                    childCell.cellPos  in [cell.cellPos for cell in openCells]) and
                    (childCell.fCost <= gCost + hCost)
                ):
                    continue

                childCell.gCost = gCost
                childCell.hCost = hCost
                childCell.fCost = gCost + hCost

                openCells += [childCell]
        log.debug(f'A* path from {startCell} to {targetCell} is {path}')
        return path

    def _computeHeadingSpeedTimeout(self, path, dotBotId):

        if path:
            log.debug(f'finding heading for path of {path}')

            dotBot                = self.dotBotsView[dotBotId]

            # find initial heading and distance to reach first cell in path (to use as reference)
            initialHeading         = (math.degrees(math.atan2(path[0][1] - dotBot['y'], path[0][0] - dotBot['x'])) + 90) % 360

            # destination center coordinates of target (if no obstacles on path) or of last cell before changing heading
            # movement is from cell centre to cell centre to avoid movements across cell borders and assure
            # passing though cells to explore them
            destination            = (path[0][0]+self.MINFEATURESIZE/4, path[0][1]+self.MINFEATURESIZE/4)

            # compute distance dotBot will move along same trajectory until heading changes from initial one
            for idx, (cx,cy) in enumerate(path):

                if (cx, cy) == path[-1]:
                    # target is the only cell in the path
                    break

                # find heading to center of next cell
                headingToNext     = (math.degrees(math.atan2(path[idx+1][1] - cy, path[idx+1][0] - cx)) + 90) % 360

                if headingToNext != initialHeading:
                    # heading changes
                    destination = (cx + self.MINFEATURESIZE/4, cy + self.MINFEATURESIZE/4)
                    break

            # find distance to destination cell from dotBot position
            distance = u.distance((dotBot['x'], dotBot['y']), destination)

            # heading to get to destination cell center (to assure exploration and avoid border to border movement)
            heading = (
                math.degrees(math.atan2(destination[1] - dotBot['y'], destination[0] - dotBot['x'])) + 90
                ) % 360

            # set speed
            speed   = 1

            # find timeout to stop at target cell
            timeout = distance/speed

            log.debug(f'destination cell is {destination}, heading {heading}, time {timeout}')

        else:
            (heading, speed, timeout) = (360*random.random(), 1, 0.5)

        return (heading, speed, timeout)

