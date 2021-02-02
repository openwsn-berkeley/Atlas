# built-in
import random
import time
import math
import threading
import copy
import time
# third-party
# local
import SimEngine
import Wireless
import Utils as u

class ExceptionOpenLoop(Exception):
    pass

class MapBuilder(object):
    '''
    A background task which consolidates the map.
    It combines dots into lines
    It declares when the map is complete.
    '''

    PERIOD         = 1 # s, in simulated time
    MINFEATURESIZE = 0.9 # shortest wall, narrowest opening

    def __init__(self):

        # store params

        # local variables
        self.simEngine       = SimEngine.SimEngine()
        self.dataLock        = threading.RLock()
        self.simRun = 1
        self.discoMap = {
            'complete': False,    # is the map complete?
            'dots':     [],       # each bump becomes a dot
            'lines':    [],       # closeby dots are aggregated into a line
        }

        # schedule first housekeeping activity
        self.simEngine.schedule(self.simEngine.currentTime()+self.PERIOD,self._houseKeeping)
        self.exploredCells = []

    #======================== public ==========================================
    def reset(self):
        self.discoMap = {
            'complete': False,    # is the map complete?
            'dots':     [],       # each bump becomes a dot
            'lines':    [],       # close by dots are aggregated into a line
        }

        # schedule first housekeeping activity
        self.simEngine.schedule(self.simEngine.currentTime()+self.PERIOD,self._houseKeeping)
        self.exploredCells = []

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
        self.simEngine.schedule(self.simEngine.currentTime()+self.PERIOD,self._houseKeeping)

        # this is where we invoke end of current simulation and trigger resest
        if self.discoMap['complete'] and self.discoMap['lines'] != [] :
            self.simRun += 1
            time.sleep(5)

    def get_explored(self, exploredCells):
        self.exploredCells = exploredCells
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
                if direction=='horizontal':
                    thesedots                = [x for (x,y) in self.discoMap['dots'] if y==ref]
                else:
                    thesedots                = [y for (x,y) in self.discoMap['dots'] if x==ref]

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

                    if vnext-v<=self.MINFEATURESIZE:

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
            if  u.distance((l1ax,l1ay),(l2ax,l2ay))<=self.MINFEATURESIZE:
                returnVal = True
                break
            if  u.distance((l1ax,l1ay),(l2bx,l2by))<=self.MINFEATURESIZE:
                returnVal = True
                break
            if  u.distance((l1bx,l1by),(l2ax,l2ay))<=self.MINFEATURESIZE:
                returnVal = True
                break
            if  u.distance((l1bx,l1by),(l2bx,l2by))<=self.MINFEATURESIZE:
                returnVal = True
                break
            break

        return returnVal

class Orchestrator(object):
    '''
    The central orchestrator of the expedition.
    '''

    def __init__(self,positions,floorplan):

        # store params
        self.positions         = positions
        self.floorplan         = floorplan


        # local variables
        self.simEngine         = SimEngine.SimEngine()
        self.wireless          = Wireless.Wireless()
        self.navAlgorithm      = None
        self.notifrec          = False #whether or not a notification has been recieved from a bot
        self.mostRecentBumpTs  = self.simEngine.currentTime() #initialise value of last known bumptime to be current time
        self.dotbotsview       = [ # the Orchestrator's internal view of the DotBots
            {
                'x':           x,
                'y':           y,
                'posTs':       0,
                'heading':     0,
                'speed':       0,
                'commandId':   0,
                'lastBump': self.mostRecentBumpTs
            } for (x,y) in self.positions
        ]
        self.mapBuilder        = MapBuilder()
        self.unexploredCells        = self.floorplan.overlayCells
        self.exploredCells = [self.positions[0]]
        self.frontierCellsTargeted = []
        self.allFrontierCellsAndDistance = []
        self.obstacle_cells = []
        self.cellsTargeted = []
        self.frontierCellsTackled = []
        self.previously_unreachable = []
        self.open_cells = [(1,1)]

    #======================== public ==========================================

    def startExploration(self):
        '''
        Simulation engine, start exploring
        '''
        for i in range(len(self.dotbotsview)):
            if self.navAlgorithm == ['Ballistic']:
                dotbot =  self.dotbotsview[i]
                dotbot['heading'] = random.randint(0,359)
                dotbot['speed']   = 1
            elif self.navAlgorithm == ['Atlas_2.0']:
                self.atlas({'dotBotId': i , 'bumpTs': None, 'posTs': None})

        self._sendDownstreamCommands('command')
        print('-----INITIAL COMMANDS SENT------')

    def setNavAlgorithm(self, navigation):
        self.navAlgorithm = navigation

    def atlas(self,msg):

        #initialize
        (sx,sy) = self.positions[0]
        self.allFrontierCellsAndDistance = []

        #======================================================================================
        # calculate new position of robot , register bump, and find which cells have been
        # explored so far
        #======================================================================================

        # if msg = initialize then we are setting up the first movement and dot have any peivous
        # info to backtrack to
        if msg['bumpTs'] == None:
            dotbot = self.dotbotsview[msg['dotBotId']]
            (rx,ry) = (sx,sy)
            print('INITIALIZING')

        else:
            # save previous position to find pervious trajectory of movement to know
            # which cells have been explored
            dotbot = self.dotbotsview[msg['dotBotId']]
            (x2, y2) = (dotbot['x'], dotbot['y'])
            # if bumptime of notification recieved is same as that of the previous notification, it means that its a
            # re-transmitted message, so x and y values remain the same, otherwise updated position values are calculated
            if msg['bumpTs'] != dotbot['lastBump']:
                dotbot['lastBump'] = msg['bumpTs']
                # compute new theoretical position, based on the bump time - the time the bot started moving after last bump/stop
                dotbot['x'] += (msg['bumpTs'] - msg['posTs']) * math.cos(math.radians(dotbot['heading'] - 90)) * dotbot[
                    'speed']
                dotbot['y'] += (msg['bumpTs'] - msg['posTs']) * math.sin(math.radians(dotbot['heading'] - 90)) * dotbot[
                    'speed']
                dotbot['posTs'] = msg['bumpTs']

                # round
                dotbot['x'] = round(dotbot['x'], 3)
                dotbot['y'] = round(dotbot['y'], 3)

                # notify the self.mapBuilder the obstacle location
                self.mapBuilder.notifBump(dotbot['x'], dotbot['y'])

            else:
                dotbot['x'] += 0
                dotbot['y'] += 0
                dotbot['posTs'] = msg['posTs']

            (rx, ry) = (dotbot['x'], dotbot['y']) #shorthand

            map = self.mapBuilder.getMap()

            # find the trajectories that all the robots have taken from last notification to now
            # check which cells the trajectories pass through
            # add these cells to explored cells
            for cell in self.floorplan.overlayCells:
                cellxmax = cell[0] + self.floorplan.overlayWidth
                cellymax = cell[1] + self.floorplan.overlayHeight
                cell_explored = self._trajectory_on_cell(rx,ry,x2,y2,cell[0],cell[1],cellxmax, cellymax)
                if cell_explored and cell not in self.exploredCells:
                    self.exploredCells += [cell]
                    openCell = True
                    if self._dot_in_cell((rx,ry), cell[0], cellxmax, cell[1], cellymax):
                        #if (rx <= cell[0] or rx >= cellxmax  or ry <= cell[1] or ry >= cellymax):
                        x_reverse = rx - (0.01) * math.cos(math.radians(dotbot['heading'] - 90)) * dotbot['speed']
                        y_reverse = ry - (0.01) * math.sin(math.radians(dotbot['heading'] - 90)) * dotbot['speed']
                        if x_reverse <= cell[0] or x_reverse >= cellxmax or y_reverse <= cell[1] or y_reverse >= cellymax:
                            openCell = False
                    if openCell:
                        self.open_cells += [cell]
                #if cell has bump dot on it add this cell to explored cells
                if map['dots']:
                    for dot in map['dots']:
                        if self._dot_in_cell(dot, cell[0], cellxmax, cell[1], cellymax):
                            if cell not in self.open_cells:
                                self.obstacle_cells += [cell]
                                self.exploredCells += [cell]

            self.obstacle_cells = list(set(self.obstacle_cells))
            self.open_cells = list(set(self.open_cells))
            print('OBSTACLES AT', self.obstacle_cells)

        #==================================================================================
        # check for Frontier Cells, [these are] :
        # - have already been explored
        # - have at least one 'avaliable' cell in their one hop neighbourhood
        # =================================================================================
        for (ex,ey) in self.open_cells:

            # if this cell is already a tackled frontier then skip
            if (ex,ey) in self.frontierCellsTackled:
                continue

            avaliable_neighbors = False
            oneHopN = self._OneHopNeighborhood(ex,ey,shuffle=False)
            for (nx,ny) in oneHopN:
                if (nx,ny) not in self.exploredCells:
                    if (nx,ny) in self.cellsTargeted:
                        self.previously_unreachable += [(nx,ny)]
                    elif (nx,ny) in self.previously_unreachable:
                        continue
                    else:
                        self.allFrontierCellsAndDistance += [((ex, ey), u.distance((ex, ey), (sx, sy)))]
                        avaliable_neighbors = True


            if not avaliable_neighbors:
                self.frontierCellsTackled += [(ex,ey)]
                continue

        self.allFrontierCellsAndDistance = list(set(self.allFrontierCellsAndDistance))

        next_move_cell = None
        if self.allFrontierCellsAndDistance:

            # find closed frontier cells (CFS) to start
            min_frontier_dist= sorted(self.allFrontierCellsAndDistance, key=lambda item: item[1])[0][1]
            frontierCells = [c for (c, d) in self.allFrontierCellsAndDistance if d == min_frontier_dist]


            #===============================================================================
            # out of all the unexplored neighbors of the closest frontier cells
            # find the ones that are reachable, as there is a possible Line of Sight
            # trajectoery connection between the robot and the cell, then out of those,
            # chose the closest to the robot as the target next
            #===============================================================================

            # filter out which surrounding cells of the frontires are suitable to move the robot to
            possible_next = []
            targets_and_distances = []
            path_open = True

            for (fx,fy) in frontierCells:
                for (nx,ny) in self._OneHopNeighborhood(fx,fy):
                    if ((nx,ny) not in self.exploredCells):
                            possible_next += [(nx,ny)]

            if possible_next:
                for (px,py) in possible_next:
                    # check if there is a direct line of sight connection between robot and cell
                    for (ox,oy) in self.obstacle_cells:
                        oxmax = ox + self.floorplan.overlayWidth
                        oymax = oy + self.floorplan.overlayHeight
                        if self._trajectory_on_cell(rx,ry,px,py,ox,oy,oxmax,oymax):
                            path_open = False
                            self.previously_unreachable += [(px,py)]
                            break

                    if path_open:
                        targets_and_distances += [((px,py),u.distance((rx,ry),(px,py)))]
                    else:
                        continue

                if targets_and_distances:
                    min_PT_dist = sorted(targets_and_distances, key=lambda item: item[1])[0][1]
                    closest_targets = [c for (c, d) in targets_and_distances if d == min_PT_dist]
                    next_move_cell = random.choice(closest_targets)

        #============================================================================================
        # if we reach this point and we dont have a next move determined, we should try to target
        # cells that were previously unreachable again
        #============================================================================================

        if not self.allFrontierCellsAndDistance or not possible_next or not targets_and_distances:
            for (pux,puy) in list(set(self.previously_unreachable)):
                if (pux,puy) in self.exploredCells:
                    continue

                for (ox, oy) in self.obstacle_cells:
                    oxmax = ox + self.floorplan.overlayWidth
                    oymax = oy + self.floorplan.overlayHeight
                    if not self._trajectory_on_cell(rx, ry, pux, puy, ox, oy, oxmax, oymax):
                        next_move_cell = (pux,puy)
                        break

        if next_move_cell == None:
            #move towards closest bump dot
            #assert next_move_cell
            if dotbot ['speed'] == 0:
                dotbot['speed'] == 1
            return

        #set next headings
        (mcx,mcy) = next_move_cell
        (tx,ty) = (random.uniform(mcx,mcx+self.floorplan.overlayWidth),
                   mcy + self.floorplan.overlayHeight)
        new_heading = self._calculate_heading(rx, ry, tx, ty)
        self.cellsTargeted += [(mcx,mcy)]

        dotbot['heading']  = new_heading

        # set the DotBot's speed
        dotbot['speed'] = 1

        # bump command Id so DotBot knows this is not a duplicate command
        dotbot['commandId'] += 1
        print('new heading', dotbot['heading'], 'target', (tx, ty))
        print(dotbot, msg['dotBotId'])
        print('...')

    def ballistic(self, msg):
        # shorthand
        dotbot = self.dotbotsview[msg['dotBotId']]

        # if bumptime of notification recieved is same as that of the previous notification, it means that its a
        # re-transmitted message, so x and y values remain the same, otherwise updated position values are calculated

        if msg['bumpTs'] != dotbot['lastBump']:
            dotbot['lastBump'] = msg['bumpTs']
            # compute new theoretical position, based on the bump time - the time the bot started moving after last bump/stop
            dotbot['x'] += (msg['bumpTs'] - msg['posTs']) * math.cos(math.radians(dotbot['heading'] - 90)) * dotbot[
                'speed']
            dotbot['y'] += (msg['bumpTs'] - msg['posTs']) * math.sin(math.radians(dotbot['heading'] - 90)) * dotbot[
                'speed']
            dotbot['posTs'] = msg['bumpTs']

            # round
            dotbot['x'] = round(dotbot['x'], 3)
            dotbot['y'] = round(dotbot['y'], 3)

        else:

            dotbot['x'] += 0
            dotbot['y'] += 0
            dotbot['posTs'] = msg['posTs']

        # notify the self.mapBuilder the obstacle location
        self.mapBuilder.notifBump(dotbot['x'], dotbot['y'])

        # adjust the heading of the DotBot which bumped (avoid immediately bumping into the same wall)
        dotbot['heading'] = random.randint(0, 359)

        # set the DotBot's speed
        dotbot['speed'] = 1

        # bump command Id so DotBot knows this is not a duplicate command
        dotbot['commandId'] += 1

    def fromDotBot(self,msg):
        '''
        A DotBot indicates its bump sensor was activated at a certain time
        '''

        #if msg['bumpTs'] == None:
        #    self._sendDownstreamCommands('command')
        #    return

        if self.navAlgorithm == ['Ballistic']:

            self.ballistic(msg)

        elif self.navAlgorithm == ['Atlas_2.0']:
            self.atlas(msg)

        # send commands to the robots
        self._sendDownstreamCommands('command')
        print('----------NEW COMMANDS SENT------------')

    def getView(self):

        # do NOT write back any results to the DotBot's state as race condition possible
        # compute updated position

        return {
            'dotbots': [
                {
                    'x': db['x']+(db['posTs'] -db['lastBump'])*math.cos(math.radians(db['heading']-90))*db['speed'],
                    'y': db['y']+(db['posTs'] -db['lastBump'])*math.sin(math.radians(db['heading']-90))*db['speed'],
                } for db in self.dotbotsview
            ],
            'discomap': self.mapBuilder.getMap(),
        }

    def reset(self):
        '''
        Reset orchestrator
        '''
        self.dotbotsview       = [ # the Orchestrator's internal view of the DotBots
            {
                'x':           x,
                'y':           y,
                'posTs':       0,
                'heading':     0,
                'speed':       0,
                'commandId':   0,
                'lastBump':    0,
            } for (x,y) in self.positions
        ]
        self.unexploredCells = self.floorplan.overlayCells
        self.exploredCells = [self.positions[0]]
        self.frontierCellsTargeted = []
        self.allFrontierCellsAndDistance = []
        self.obstacle_cells = []
        self.cellsTargeted = []
        self.frontierCellsTackled = []
        self.previously_unreachable = []
        self.open_cells = [(1,1)]


    #======================== private =========================================

    def _sendDownstreamCommands(self, type):
        '''
        Send the next heading and speed commands to the robots
        '''

        # format msg
        msg = [
            {
                'commandId': dotbot['commandId'],
                'heading':   dotbot['heading'],
                'speed':     dotbot['speed'],
                'type':      type
            } for dotbot in self.dotbotsview
        ]

        # hand over to wireless
        self.wireless.toDotBots(msg)

    def _OneHopNeighborhood(self, x, y, shuffle=True):
        returnVal = []
        for (nx, ny) in [
            (x - 0.5, y - 0.5), (x , y-0.5), (x + 0.5, y - 0.5),
            (x - 0.5, y),                    (x + 0.5, y ),
            (x - 0.5, y + 0.5), (x , y+0.5), (x + 0.5, y + 0.5),
        ]:

            # only consider cells inside the realMap
            if (
                    (nx >= 0) and
                    (ny < self.floorplan.height) and
                    (ny >= 0) and
                    (nx < self.floorplan.width)
            ):
                returnVal += [(nx, ny)]

        if shuffle:
            random.shuffle(returnVal)
        return returnVal

    def _TwoHopNeighborhood(self, x, y):
        returnVal = []
        for (nx, ny) in [
            (x - 1, y - 1), (x - 0.5, y - 1), (x , y-1), (x + 0.5, y - 1), (x + 1 , y - 1),
            (x - 1, y - 0.5),                                              (x + 1, y - 0.5),
            (x - 1, y),                                                    (x + 1, y  ),
            (x + 0.5, y - 0.5),                                            (x + 1, y + 0.5),
            (x - 1, y + 1), (x - 0.5 , y + 1), (x, y+1), (x + 0.5, y + 1), (x + 1, y + 1)
        ]:

            # only consider cells inside the realMap
            if (
                    (nx >= 0) and
                    (ny < self.floorplan.height) and
                    (ny >= 0) and
                    (nx < self.floorplan.width)
            ):
                returnVal += [(nx, ny)]

        random.shuffle(returnVal)
        return returnVal

    def _dot_in_cell(self,dot, cellXmin, cellXmax, cellYmin, cellYmax ):
        (x_dot, y_dot) = dot
        if (x_dot >= cellXmin and x_dot <= cellXmax) and (y_dot >= cellYmin and y_dot <= cellYmax):
            return True
        else:
            return False

    def _oneStepCloser(self, rx, ry, tx, ty):
        (nx, ny) = (None, None)
        min_dist = None
        for (x, y) in self._OneHopNeighborhood(rx, ry, shuffle=True):
            known_map = self.mapBuilder.getMap()
            cell_has_obstacle = False
            for dot in known_map['dots']:
                if self._dot_in_cell(dot, x, y, x + self.floorplan.overlayWidth, y + self.floorplan.overlayHeight):
                    cell_has_obstacle = True
                    break

            #no walls and no robots
            if (
                    not cell_has_obstacle  and
                    (x, y) not in self.dotbotsview

            ):
                distToTarget = u.distance((x, y), (tx, ty))
                if (
                        min_dist == None or
                        distToTarget < min_dist
                ):
                    min_dist = distToTarget
                    (nx, ny) = (x, y)
        return (nx, ny)

    def _trajectory_on_cell(self, rx, ry, x2, y2, ax, ay, bx, by):
        # initial calculations (see algorithm)
        deltax = x2 - rx
        deltay = y2 - ry
        #                         left      right     bottom        top
        p = [-deltax, deltax, -deltay, deltay]
        q = [rx - ax, bx - rx, ry - ay, by - ry]

        # initialize u1 and u2
        u1 = 0
        u2 = 1

        # iterating over the 4 boundaries of the obstacle in order to find the t value for each one.
        # if p = 0 then the trajectory is parallel to that boundary
        # if p = 0 and q<0 then line completly outside boundaries

        # update u1 and u2
        for i in range(4):

            # abort if line outside of boundary

            if p[i] == 0:
                # line is parallel to boundary i

                if q[i] < 0:
                    return False
                pass  # nothing to do
            else:
                t = q[i] / p[i]
                if (p[i] < 0 and u1 < t):
                    u1 = t
                elif (p[i] > 0 and u2 > t):
                    u2 = t

        # if I get here, u1 and u2 should be set
        assert u1 is not None
        assert u2 is not None

        # decide what to return
        if (u1 > 0 and u1 < u2 and u2 < 1) or (0 < u1 < 1 and u1<u2) or (0 < u2 < 1 and u1<u2):
            return True
        else:
            return False

    def _calculate_heading(self, rx,ry,target_x,target_y):
        heading = (math.atan2(target_y-ry, target_x-rx) * 180.0 / math.pi + 180)-90
        if heading < 0:
            heading = (360-abs(heading))
        if heading > 360:
            heading  = (heading - 360) + 90
        return heading

