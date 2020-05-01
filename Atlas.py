'''
Atlas: Exploration and Mapping with a Sparse Swarm of Networked IoT Robots
'''

#=== built-in
import os
import time
import random
import math
import json
import pprint
import datetime
#=== third-party
#=== local
import AtlasScenarios

#============================ defines =========================================

#=== settings

SCENARIOS          = [
    'scenario_floorplan',
    'scenario_canonical',
    'scenario_empty',
    #'scenario_mini_floorplan',
    #'scenario_mini_canonical',
    #'scenario_mini_empty',
    #'scenario_tiny_1',
    #'scenario_tiny_2',
]
NUM_ROBOTS         = [10,20,30,40,50,60,70,80,90,100]
NUMCYCLES          = 200
UI                 = False

#=== defines

VERSION            = (1,2)

HEADING_N          = 'N'
HEADING_NE         = 'NE'
HEADING_E          = 'E'
HEADING_SE         = 'SE'
HEADING_S          = 'S'
HEADING_SW         = 'SW'
HEADING_W          = 'W'
HEADING_NW         = 'NW'
HEADING_ALL        = [
    HEADING_N, 
    HEADING_NE,
    HEADING_E,
    HEADING_SE,
    HEADING_S,
    HEADING_SW,
    HEADING_W,
    HEADING_NW,
]

#============================ variables =======================================

pp =  pprint.PrettyPrinter(depth=3,compact=True)

#============================ helper functions ================================

def genRealMapDrawing(drawing):
    realMap   = []
    startPos  = None
    row       = 0
    col       = 0
    for line in drawing.splitlines():
        if not line.startswith('#'):
            continue
        realMap += [[]]
        for c in line:
            if   c=='#':
                realMap[-1] += [0]
            elif c==' ':
                realMap[-1] += [1]
            elif c=='S':
                realMap[-1] += [1]
                assert startPos==None
                startPos = (row,col)
            else:
                raise SystemError()
            col   += 1
        row  += 1
        col   = 0
    return (realMap,startPos)

def printDiscoMap(discoMap,startPos,robotPositions,kpis):
    output         = []
    numUnExplored  = 0
    output        += ['']
    numRows        = len(discoMap)
    numCols        = len(discoMap[0])
    numCells       = numRows*numCols
    for row in range(len(discoMap)):
        line = []
        for col in range(len(discoMap[row])):
            while True:
                # robot
                robotFound = False
                for (ri,(rx,ry)) in enumerate(robotPositions):
                    if (row,col) == (rx,ry):
                        robotFound = True
                        line += [str(ri%10)]
                        break
                if robotFound:
                    break
                # start position
                if (row,col)==startPos:
                    line += ['S']
                    break
                # wall
                if  discoMap[row][col]==0:
                    line += ['#']
                    break
                # unexplored
                if discoMap[row][col]==-1:
                    numUnExplored += 1
                    line += ['.']
                    break
                # explored
                line += [' ']
                break
        output += [' '.join(line)]
    output += ['']
    output += [
        'numExplored  : {0}/{1} ({2:.0f}%)'.format(
            numCells-numUnExplored,numCells,100.0*((numCells-numUnExplored)/numCells)
        )
    ]
    for k in sorted(kpis.keys()):
        output += ['{0:<13}: {1}'.format(k,kpis[k])]
    output = '\n'.join(output)
    os.system('cls')
    print(output)

#============================ classes =========================================

#======== exceptions

class MappingDoneSuccess(Exception):
    pass

class MappingDoneIncomplete(Exception):
    pass

#======== navigation algorithms

class Navigation(object):
    def __init__(self,realMap,startPos,numRobots):
        
        # store params
        self.realMap                   = realMap
        self.startPos                  = startPos
        self.numRobots                 = numRobots
        
        # local variablels
        self.numRows                   = len(self.realMap)    # shorthand
        self.numCols                   = len(self.realMap[0]) # shorthand
        self.firstIteration            = True
        self.rankMaps                  = {}
        self.discoMap                  = []
        self.allCellsIdx               = []
        self.stats                     = {}
        for (x,row) in enumerate(realMap):
            self.discoMap             += [[]]
            for (y,col) in enumerate(row):
                self.discoMap[-1]     += [-1]
                self.allCellsIdx      += [(x,y)]
    
    def getStats(self):
        return self.stats
    
    def _moveRobot(self,robotIdx,newx,newy):
        self.robotPositions[robotIdx] = (newx,newy)
        self.robotsMoved             += [robotIdx]
        
        # update discoMap
        for (x,y) in self._OneHopNeighborhood(newx,newy,shuffle=False):
            if self.discoMap[x][y]==-1:
                self.numExplored += 1
            if   self.realMap[x][y] == 0:
                self.discoMap[x][y]=0
            elif self.realMap[x][y] == 1:
                self.discoMap[x][y]=1
            else:
                raise SystemError()
    
    def _determineDoneExploring(self):
        fullDiscoMap = True
        for row in self.discoMap:
            for cell in row:
                if cell == -1:
                    fullDiscoMap = False
                    break
        if fullDiscoMap:
            raise MappingDoneSuccess
    
    def _OneHopNeighborhood(self,x,y,shuffle=True):
        returnVal = []
        for (nx,ny) in [
                (x-1,y-1),(x-1,y  ),(x-1,y+1),
                (x  ,y-1),          (x  ,y+1),
                (x+1,y-1),(x+1,y  ),(x+1,y+1),
            ]:
            
            # only consider cells inside the realMap
            if  (
                    (nx>=0)            and
                    (nx<self.numRows)  and
                    (ny>=0)            and
                    (ny<self.numCols)
                ):
                returnVal += [(nx,ny)]
        
        if shuffle:
            random.shuffle(returnVal)
        return returnVal
    
    def _TwoHopNeighborhood(self,x,y):
        returnVal = []
        for (nx,ny) in [
                (x-2,y-2),(x-2,y-1),(x-2,y  ),(x-2,y+1),(x-2,y+2),
                (x-1,y-2),                              (x-1,y+2),
                (x  ,y  ),                              (x  ,y+2),
                (x+1,y-2),                              (x+1,y+2),
                (x+2,y-2),(x+2,y-1),(x+2,y  ),(x+2,y+1),(x+2,y+2)
            ]:
            
            # only consider cells inside the realMap
            if  (
                    (nx>=0)            and
                    (nx<self.numRows)  and
                    (ny>=0)            and
                    (ny<self.numCols)
                ):
                returnVal += [(nx,ny)]
        
        random.shuffle(returnVal)
        return returnVal

#=== distributed

class NavigationDistributed(Navigation):

    def think(self, robotPositions):
        
        # initialize variables
        self.robotPositions       = robotPositions[:] # make a local copy
        self.robotsMoved          = []
        self.numExplored          = 0
        
        # determine whether we're done exploring
        self._determineDoneExploring()
        
        # move each robot
        for (ridx,(rx,ry)) in enumerate(robotPositions):
            
            # determine validNextPositions
            validNextPositions = []
            for (nx,ny) in self._OneHopNeighborhood(rx,ry):
                if  (
                        (self.realMap[nx][ny]==1)   and         # no wall
                        ((nx,ny) not in self.robotPositions)    # no robot
                    ):
                    validNextPositions += [(nx,ny)]
            
            # pick next position and move
            if validNextPositions:
                (newx,newy) = self._pickNextPosition(ridx,rx,ry,validNextPositions)
                self._moveRobot(ridx,newx,newy)
        
        return (self.robotPositions,self.discoMap,self.numExplored)
    
    def _pickNextPosition(self,ridx,rx,ry,validNextPositions):
        raise SystemError()
    
class NavigationRandomWalk(NavigationDistributed):
    
    def _pickNextPosition(self,ridx,rx,ry,validNextPositions):
        return random.choice(validNextPositions)

class NavigationBallistic(NavigationDistributed):

    def __init__(self,realMap,startPos,numRobots):
        NavigationDistributed.__init__(self,realMap,startPos,numRobots)
        self.robotHeading = []
        for _ in range(self.numRobots):
            self.robotHeading += [random.choice(HEADING_ALL)]

    def _pickNextPosition(self,ridx,rx,ry,validNextPositions):
        
        nextPosition = None
        
        while not nextPosition:
            # compute next position
            # FIXME: box
            if   self.robotHeading[ridx]==HEADING_N:
                nextPosition = (rx-1,ry  )
            elif self.robotHeading[ridx]==HEADING_NE:
                nextPosition = (rx-1,ry+1)
            elif self.robotHeading[ridx]==HEADING_E:
                nextPosition = (rx  ,ry+1)
            elif self.robotHeading[ridx]==HEADING_SE:
                nextPosition = (rx+1,ry+1)
            elif self.robotHeading[ridx]==HEADING_S:
                nextPosition = (rx+1,ry  )
            elif self.robotHeading[ridx]==HEADING_SW:
                nextPosition = (rx+1,ry-1)
            elif self.robotHeading[ridx]==HEADING_W:
                nextPosition = (rx  ,ry-1)
            elif self.robotHeading[ridx]==HEADING_NW:
                nextPosition = (rx-1,ry-1)
            else:
                raise SystemError()
            
            if nextPosition not in validNextPositions:
                self.robotHeading[ridx] = random.choice(HEADING_ALL)
                nextPosition = None
        
        return nextPosition

#=== centralized

class NavigationCentralized(Navigation):
    
    def __init__(self,realMap,startPos,numRobots):
        Navigation.__init__(self,realMap,startPos,numRobots)
        self.shouldvisits         = {}
        self._distance(startPos) # force rankMap to be fully built for start position
    
    def _distance(self,pos1,pos2=None):
        
        # easy answer if same position
        if pos1==pos2:
            return 0
        
        # inverting pos1 and pos2 in case pos2 already cached (same distance)
        if (pos1 not in self.rankMaps) and (pos2 in self.rankMaps):
            temp = pos1
            pos1 = pos2
            pos2 = temp
        
        # check whether rankMaps in cache, otherwise build or resume
        if  (
                (pos1 in self.rankMaps) and
                (pos2 in self.rankMaps[pos1])
            ):
                # stats
                self._stats_incr('cache_hit')
        else:
            if  (
                    (pos1 in self.rankMaps) and
                    (pos2 not in self.rankMaps[pos1])
                ):
                # resuming building the rankMap
                
                # stats
                self._stats_incr('cache_miss_resume')
                
                # local variables (resume)
                rankMap                   = self.rankMaps[pos1]
                shouldvisit               = self.shouldvisits[pos1]
            else:
                # starting new rankMap
                
                # stats
                self._stats_incr('cache_miss_new')
                
                # local variables (new)
                rankMap                   = {}
                shouldvisit               = []
                
                # start from start position
                rankMap[pos1]             = 0
                shouldvisit              += [pos1]
            
            while True:
                
                # find cell to visit with lowest rank (abort if none)
                found         = False
                currentrank   = None
                for (x,y) in shouldvisit:
                    if  (
                            currentrank==None or
                            rankMap[(x,y)]<currentrank
                        ):
                        currentrank   = rankMap[(x,y)]
                        (cx,cy)       = (x,y)
                        found = True
                if found==False:
                    break
                
                # assign a height for all its neighbors
                for (nx,ny) in self._OneHopNeighborhood(cx,cy):
                    if (nx,ny) in rankMap:
                        assert rankMap[(nx,ny)] <= currentrank+1 
                    if  (
                            (self.realMap[nx][ny]==1) and
                            ((nx,ny) not in rankMap)
                        ):
                        rankMap[(nx,ny)]     = currentrank+1
                        shouldvisit        += [(nx,ny)]
                
                # mark a visited
                shouldvisit.remove((cx,cy))
                
                # abort if I reached pos2
                if pos2 and (pos2 in rankMap):
                    self.shouldvisits[pos1] = shouldvisit
                    break
            
            self.rankMaps[pos1] = rankMap

        if pos2:
            return self.rankMaps[pos1][pos2]

    def _stats_incr(self,k):
        if k not in self.stats:
            self.stats[k] = 0
        self.stats[k] += 1

class NavigationRamaithitima(NavigationCentralized):
    
    def __init__(self,realMap,startPos,numRobots):
        NavigationCentralized.__init__(self,realMap,startPos,numRobots)
        self.targetFrontierbots   = []
    
    def think(self, robotPositions):
        
        # initialize variables
        self.robotPositions       = robotPositions[:] # make a local copy
        self.robotsMoved          = []
        self.numExplored          = 0
        
        # determine whether we're done exploring
        self._determineDoneExploring()
        
        # step 0: move all non-frontier robot
        catchup = False
        moved   = True
        while moved:
            moved = self._moveNonFrontierBot()
            if moved:
                catchup = True
        
        if not catchup:
            # step 1: move all frontier     robots
            moved = True
            while moved:
                moved = self._moveFrontierBot()
            self.targetFrontierbots = self._findFrontierBotIdxs()
            
            # step 2: move all non-frontier robot
            moved = True
            while moved:
                moved = self._moveNonFrontierBot()
        
        # break if couldn't move any robot
        if self.robotsMoved==[]:
            raise MappingDoneIncomplete()
        
        return (self.robotPositions,self.discoMap,self.numExplored)
    
    def _moveFrontierBot(self):
        moved = False
        while True:
            
            # find all new frontier robots
            frontierBotIdxs = self._findFrontierBotIdxs(exceptIdxs=self.robotsMoved)
            if not frontierBotIdxs:
                break
            
            # move the robot closest to the start position
            self._moveClosestFrontierbot(frontierBotIdxs)
            moved              = True
            
            break
        return moved
    
    def _findFrontierBotIdxs(self,exceptIdxs=[]):
        returnVal = []
        
        self.frontierBotNextHops = {}
        
        for (ridx,(rx,ry)) in enumerate(self.robotPositions):
            
            # don't consider robots in exceptIdxs
            if ridx in exceptIdxs:
                continue
            
            # check that robot has the frontier in its reachable 2-neighborhood
            for (nx,ny) in self._TwoHopNeighborhood(rx,ry):
                if  self.discoMap[nx][ny]==-1:
                    nr       = set(self._OneHopNeighborhood(rx,ry))
                    nn       = set(self._OneHopNeighborhood(nx,ny))
                    inter    = nr.intersection(nn)
                    nexthops = []
                    for (x,y) in inter:
                        if self.realMap[x][y]==1:
                            nexthops += [(x,y)]
                    if nexthops:
                        self.frontierBotNextHops[ridx] = random.choice(nexthops)
                        returnVal += [ridx]
                        break
        
        return returnVal
    
    def _moveClosestFrontierbot(self,candidateRobotIdxs):
        
        # pick the robot closest to the start position
        distanceToStart = {}
        for ridx in candidateRobotIdxs:
            (x,y) = self.robotPositions[ridx] # shorthand
            distanceToStart[ridx] = self._distance(self.startPos,(x,y))
        closestBotIdx = sorted(distanceToStart.items(), key=lambda item: item[1])[0][0]
        (nx,ny) = self.frontierBotNextHops[closestBotIdx]
        
        # move the closestBot
        self._moveRobot(closestBotIdx,nx,ny)
    
    def _moveNonFrontierBot(self):
        moved = False
        
        # iterate through all robots until could move one
        for (ridx,(rx,ry)) in enumerate(self.robotPositions):
        
            # break if no more frontierbots
            if not self.targetFrontierbots:
                break
            
            # don't consider frontier robots
            if ridx in self.targetFrontierbots:
                continue
            
            # don't consider robots already explored
            if ridx in self.robotsMoved:
                continue
            
            # pick a random closest frontier robot
            distances = {}
            for fidx in self.targetFrontierbots:
                distances[fidx] = self._distance(self.robotPositions[ridx],self.robotPositions[fidx])
            targetFrontierIdx = sorted(distances.items(), key=lambda item: item[1])[0][0]
            
            # attempt to move closer to target frontier robot
            (fx,fy) = self.robotPositions[targetFrontierIdx] # shorthand
            for (nx,ny) in self._OneHopNeighborhood(rx,ry):
                if  (
                        self.realMap[nx][ny]==1               and # open
                        ((nx,ny) not in self.robotPositions)  and # no robots
                        (nx,ny)!=self.startPos                and # not start position
                        self._distance((nx,ny),(fx,fy))<self._distance((rx,ry),(fx,fy))
                    ):
                    
                    # move robot
                    self._moveRobot(ridx,nx,ny)
                    moved         = True
                    
                    break
        
        return moved

class NavigationAtlas(NavigationCentralized):
    
    def think(self, robotPositions):
        
        # initialize variables
        self.robotPositions       = robotPositions[:] # make a local copy
        self.robotsMoved          = []
        self.numExplored          = 0
        
        # local variables
        frontierCellsTargeted     = []
        
        (sx,sy)                   = self.startPos # shorthand
        
        # determine whether we're done exploring
        try:
            self._determineDoneExploring()
        except:
            self.stats['num_cache_entries'] = len(self.rankMaps)
            l = [len(v) for (k,v) in self.rankMaps.items()]
            self.stats['cache_maxlength']   = max(l)
            self.stats['cache_minlength']   = min(l)
            self.stats['cache_avglength']   = float(sum(l))/len(l)
            raise
        
        #=== step 1. Move robots towards frontiercells
        
        while True:
            if self.firstIteration:
                # this is my first iteration: put robot 0 in the start position
                
                mr_idx                = 0
                (mx_next,my_next)     = self.startPos
                self.firstIteration   = False
            
            else:
                # I already have robots in the area
                
                # identify all remaining frontierCells
                allFrontierCellsAndDistance = []
                for (x,y) in self.allCellsIdx:
                    # don't consider the same call twice
                    if (x,y) in frontierCellsTargeted:
                        continue
                    # consider only open cells
                    if self.discoMap[x][y]!=1:
                        continue
                    # check wether this cell has unexplored neighbor cells
                    for (nx,ny) in self._OneHopNeighborhood(x,y,shuffle=False):
                        if self.discoMap[nx][ny]==-1:
                            allFrontierCellsAndDistance += [((x,y),self._distance((sx,sy),(x,y)))]
                            break
                
                # abort if no more frontier cells
                if not allFrontierCellsAndDistance:
                    break
                
                # keep only frontierCells with lowest rank
                minRankFrontier = sorted(allFrontierCellsAndDistance, key=lambda item: item[1])[0][1]
                frontierCells   = [c for (c,d) in allFrontierCellsAndDistance if d==minRankFrontier]
                
                # pick move robot (mv) and frontier cell (fc) to move towards
                #   Rules (most important first):
                #     - robot as close as possible to one of the target frontier cells
                #     - robot as close as possible to start position
                #     - frontier cell with many neighbors with a higher rank (avoids cutting corners)
                #     - frontier cell with many unexplored neighbors
                mr_idx                          = None
                fc_pos                          = None
                mr_distToStart                  = None
                mr_distToFc                     = None
                for (ridx,(rx,ry)) in enumerate(self.robotPositions):
                    
                    # don't move the same robot twice
                    if ridx in self.robotsMoved:
                        continue
                    
                    rDistToStart                = self._distance((sx,sy),(rx,ry))
                    max_numHigherRankNeighbors  = None
                    max_numUnexploredNeighbors  = None
                    for (fx,fy) in frontierCells:
                        rDistToFc               = self._distance((fx,fy),(rx,ry))
                        (numHigherRankNeighbors,numUnexploredNeighbors)  = self._numHigherRankAndUnexploredNeighbors(fx,fy)
                        if  (
                                mr_idx==None                   or
                                rDistToFc<mr_distToFc          or
                                (
                                    rDistToFc==mr_distToFc               and
                                    rDistToStart<mr_distToStart
                                )                              or
                                (
                                    rDistToFc==mr_distToFc               and
                                    rDistToStart==mr_distToStart         and
                                    max_numHigherRankNeighbors!=None     and
                                    numHigherRankNeighbors>max_numHigherRankNeighbors
                                )                              or
                                (
                                    rDistToFc==mr_distToFc               and
                                    rDistToStart==mr_distToStart         and
                                    max_numUnexploredNeighbors!=None     and
                                    numUnexploredNeighbors>max_numUnexploredNeighbors
                                )
                            ):
                            mr_idx                     = ridx
                            fc_pos                     = (fx,fy)
                            mr_distToStart             = rDistToStart
                            mr_distToFc                = rDistToFc
                            max_numHigherRankNeighbors = numHigherRankNeighbors
                            max_numUnexploredNeighbors = numUnexploredNeighbors
                
                # abort if couldn't find robot to move
                if mr_idx==None:
                    break
                
                # pick new position
                (mx_cur, my_cur)       = self.robotPositions[mr_idx] # shorthand
                (fx,fy)                = fc_pos                      # shorthand
                (mx_next,my_next)      = self._oneStepCloser(mx_cur,my_cur,fx,fy) 
                
                # abort if no way forward
                if (mx_next,my_next)==(None,None):
                    break
                
                frontierCellsTargeted += [fc_pos]
            
            # move moveRobot
            self._moveRobot(mr_idx,mx_next,my_next)
        
        #=== step 2. Move remaining robots to center of gravity of frontiercells
        
        while True: # fake loop
            
            # identify all frontierCells
            frontierCells = []
            for (x,y) in self.allCellsIdx:
                # consider only open cells
                if self.discoMap[x][y]!=1:
                    continue
                # check wether this cell has unexplored neighbor cells
                for (nx,ny) in self._OneHopNeighborhood(x,y,shuffle=False):
                    if self.discoMap[nx][ny]==-1:
                        frontierCells += [(x,y)]
                        break
            
            # abort if no frontiercell (end of mapping)
            if frontierCells==[]:
                break
            
            # compute CG coordinates
            cgxs = [x for (x,y) in frontierCells]
            cgx  = int(float(sum(cgxs))/len(cgxs))
            cgys = [y for (x,y) in frontierCells]
            cgy  = int(float(sum(cgys))/len(cgys))
            
            # artificially move CG if falls on wall (distance calculation would fails)
            if self.realMap[cgx][cgy]==0:
                (cgx,cgy) = frontierCells[0]
            
            # move robots
            for (ridx,(rx,ry)) in enumerate(self.robotPositions):
                
                # don't move the ones already moved in step 1
                if ridx in self.robotsMoved:
                    continue
                
                # pick new position
                (xcur, ycur)       = self.robotPositions[ridx] # shorthand
                (xnext,ynext)      = self._oneStepCloser(xcur,ycur,cgx,cgy)
                
                # abort if no way forward
                if (xnext,ynext)==(None,None):
                    continue
                
                # move
                self._moveRobot(ridx,xnext,ynext)
            
            # end of fake loop
            break
        
        return (self.robotPositions,self.discoMap,self.numExplored)
    
    def _oneStepCloser(self,sx,sy,tx,ty):
        (nx,ny)    = (None,None)
        min_dist   = None
        for (x,y) in self._OneHopNeighborhood(sx,sy,shuffle=True):
            if (
                self.realMap[x][y]==1              and # no walls
                (x,y) not in self.robotPositions       # no robots
            ):
                distToTarget = self._distance((x,y),(tx,ty))
                if (
                    min_dist==None or
                    distToTarget<min_dist
                ):
                    min_dist = distToTarget
                    (nx,ny) = (x,y)
        return (nx,ny)
    
    def _numHigherRankAndUnexploredNeighbors(self,x,y):
        numHigherRankNeighbors = 0
        numUnexploredNeighbors = 0
        rankMap = self.rankMaps[self.startPos] # shorthand
        for (nx,ny) in self._OneHopNeighborhood(x,y,shuffle=False):
            if  (
                    self.discoMap[nx][ny]==1 and
                    rankMap[(nx,ny)]>rankMap[(x,y)]
                ):
                numHigherRankNeighbors += 1
            if self.discoMap[nx][ny]==-1:
                numUnexploredNeighbors += 1
        return (numHigherRankNeighbors,numUnexploredNeighbors)

#======== core simulator

'''
calculates steps taken from source to destination
'''

def singleExploration(cycleId,scenarioName,realMap,startPos,NavAlgClass,numRobots,collectHeatmap):
    navAlg                   = NavAlgClass(realMap,startPos,numRobots)
    robotPositions           = [startPos]*numRobots
    if collectHeatmap:
        heatmap              = []
        for (x,row) in enumerate(realMap):
            heatmap         += [[]]
            for (y,cell) in enumerate(row):
                if cell==0:
                    heatmap[-1]  += [-1]
                else:
                    heatmap[-1]  += [ 0]
        (sx,sy)              = startPos
    
    numExplored          = 0
    profile              = []
    
    kpis                     = {
        'scenarioName': scenarioName,
        'navAlg':       NavAlgClass.__name__,
        'numTicks':     0,
        'numSteps':     0,
        'numRobots':    numRobots,
        'version':      '.'.join([str(n) for n in VERSION]),
    }
    
    while True:
        
        # think
        try:
            (nextRobotPositions,discoMap,numNewExplored) = navAlg.think(robotPositions)
        except MappingDoneSuccess:
            kpis['mappingoutcome'] = 'success'
            break
        except MappingDoneIncomplete:
            kpis['mappingoutcome'] = 'incomplete'
            break
        
        # move
        for (i,(nx,ny)) in enumerate(nextRobotPositions):
            (cx,cy) = robotPositions[i]
            if (nx,ny) != (cx,cy):
                kpis['numSteps'] += 1
            if collectHeatmap:
                assert heatmap[nx][ny]>=0
                heatmap[nx][ny] += 1
            robotPositions[i] = nextRobotPositions[i]
        
        # update KPIs
        kpis['numTicks']    += 1
        numExplored         += numNewExplored
        profile             += [numExplored]
        
        # print
        if UI:
            printDiscoMap(discoMap,startPos,robotPositions,kpis)
        
        #input()
    
    if collectHeatmap:
        kpis['heatmap']      = heatmap
    kpis['profile']          = profile
    kpis['navStats']         = navAlg.getStats()
    
    return kpis

#============================ main ============================================

def main():

    NavAlgClasses  = [
        NavigationRamaithitima,
        NavigationAtlas,
        NavigationRandomWalk,
        NavigationBallistic,
    ]
    
    startTime = time.time()
    
    with open('AtlasLog_{0}.json'.format(time.strftime("%y%m%d%H%M%S",time.localtime(startTime))).format(),'a') as f:
    
        for cycleId in range(NUMCYCLES):
            
            cycleStart = time.time()
            
            for numRobots in NUM_ROBOTS:
                
                if cycleId==0 and numRobots==max(NUM_ROBOTS):
                    collectHeatmap = True
                else:
                    collectHeatmap = False
                
                for scenarioName in SCENARIOS:

                    # create the realMap
                    (realMap,startPos) = genRealMapDrawing(getattr(AtlasScenarios,scenarioName))
                    
                    # execute the simulation for each navigation algorithm
                    for NavAlgClass in NavAlgClasses:
                        
                        # only 1 cycle for Atlas (deterministic)
                        if NavAlgClass==NavigationAtlas and cycleId>0:
                            continue
                        
                        kpis               = []
                        
                        # run single run
                        start_time         = time.time()
                        kpis               = singleExploration(cycleId,scenarioName,realMap,startPos,NavAlgClass,numRobots,collectHeatmap)
                        print(
                            'cycleId={0:>3} numRobots={1:>3} scenarioName={2:>30} NavAlgClass={3:>30} done in {4:>8.03f} s'.format(
                                cycleId,
                                numRobots,
                                scenarioName,
                                NavAlgClass.__name__,
                                time.time()-start_time,
                            )
                        )
                        
                        # log KPIs
                        kpis['cycleId']   = cycleId
                        f.write(json.dumps(kpis)+'\n')
                        f.flush()
            
            print(
                '   full cycle {0:>3} done in {1:>10.03f} s (simulation has been running for {2})'.format(
                    cycleId,
                    time.time()-cycleStart,
                    str(datetime.timedelta(seconds=time.time()-startTime)),
                )
            )
    
    print('Done.')

if __name__=='__main__':
    main()
