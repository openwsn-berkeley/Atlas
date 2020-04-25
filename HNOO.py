'''
simulation of navigation algorithms for micro-robots
'''

import os
import random
import cProfile

#============================ defines =========================================

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

#============================ helper functions ================================

def genGrid():
    rows  = 40
    cols  = 40
    grid  = []
    for row in range(rows):
        thisRow = []
        for col in range(cols):
            if random.random()<0.10:
                thisRow += [0]
            else:
                thisRow += [1]
        grid += [thisRow]
    sx = int(rows/2)
    sy = int(cols/2)
    startPos = (sx,sy)
    grid[sx][sy] = 1 # avoid invalid grid with obstacle at start position
    '''
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    startPos = (10,20)
    '''
    return (grid,startPos)

def printGrid(discoMap,startPos,robotPositions,kpis,rank=None):
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
                        if rank:
                            line += ['*']
                        else:
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
                # rank
                if rank:
                    line += [str(rank[row][col]%10)]
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
    def __init__(self,grid,startPos,numRobots):
        
        # store params
        self.grid            = grid
        self.startPos        = startPos
        self.numRobots       = numRobots
        
        # local variablels
        self.numRows         = len(self.grid)    # shorthand
        self.numCols         = len(self.grid[0]) # shorthand
        self.firstIteration  = True
        self.rankMaps        = {}
        self.discoMap        = []
        self.allCellsIdx     = []
        for (x,row) in enumerate(grid):
            self.discoMap   += [[]]
            for (y,col) in enumerate(row):
                self.discoMap[-1] += [-1]
                self.allCellsIdx  += [(x,y)]
    
    def _determineDoneExploring(self):
        fullDiscoMap = True
        for row in self.discoMap:
            for cell in row:
                if cell == -1:
                    fullDiscoMap = False
                    break
        if fullDiscoMap:
            raise MappingDoneSuccess
    
    def _OneHopNeighborhood(self,x,y):
        returnVal = []
        for (nx,ny) in [
                (x-1,y-1),(x-1,y  ),(x-1,y+1),
                (x  ,y-1),          (x  ,y+1),
                (x+1,y-1),(x+1,y  ),(x+1,y+1),
            ]:
            
            # do not consider cells outside the grid
            if  (
                    (nx<0)              or
                    (nx>=self.numRows)  or
                    (ny<0)              or
                    (ny>=self.numCols)
                ):
                continue
            
            returnVal += [(nx,ny)]
        return returnVal
    
    def _TwoHopNeighborhood(self,x,y):
        returnVal = []
        for (nx,ny) in [
                (x-2,y-2),(x-2,y-1),(x-2,y  ),(x-2,y+1),(x-2,y+2),
                (x-1,y+1),                              (x-1,y+2),
                (x  ,y  ),                              (x  ,y+2),
                (x+1,y-1),                              (x+1,y+2),
                (x+2,y-2),(x+2,y-1),(x+2,y  ),(x+2,y+1),(x+2,y+2)
            ]:
            
            # do not consider cells outside the grid
            if  (
                    (nx<0)         or
                    (nx>=self.numRows)  or
                    (ny<0)         or
                    (ny>=self.numCols)
                ):
                continue
            
            returnVal += [(nx,ny)]
        return returnVal

class NavigationDistributed(Navigation):

    def think(self, robotPositions):
        
        # returnVal
        nextRobotPositions   = []
        
        # determine whether we're done exploring
        self._determineDoneExploring()
        
        # move each robot
        for (ridx,(rx,ry)) in enumerate(robotPositions):
            
            # explore your neighborhood
            validNextPositions = []
            
            for (nx,ny) in self._OneHopNeighborhood(rx,ry):
                
                # populate the discovered map
                if   self.grid[nx][ny] == 0:
                    self.discoMap[nx][ny]=0
                elif self.grid[nx][ny] == 1:
                    self.discoMap[nx][ny]=1
                
                # a valid next position is one with no wall or robot
                if  (
                        (self.grid[nx][ny]==1) and
                        ((nx,ny) not in nextRobotPositions)
                    ):
                    validNextPositions += [(nx,ny)]
            
            # move robot to randomly chosen valid neighbor
            if validNextPositions:
                nextRobotPositions += [self._pickNextPosition(ridx,rx,ry,validNextPositions)]
            else:
                nextRobotPositions += [(rx,ry)]
        
        return (nextRobotPositions,self.discoMap,None)
    
    def _pickNextPosition(self,ridx,rx,ry,validNextPositions):
        raise SystemError()
    
class NavigationRandomWalk(NavigationDistributed):
    
    def _pickNextPosition(self,ridx,rx,ry,validNextPositions):
        return random.choice(validNextPositions)

class NavigationBallistic(NavigationDistributed):

    def __init__(self,grid,startPos,numRobots):
        NavigationDistributed.__init__(self,grid,startPos,numRobots)
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

class NavigationRama(Navigation):

    def think(self, robotPositions):
        
        # store params
        robotPositions            = robotPositions[:] # many a local copy
        
        # local variables
        robotsMoved               = []
        frontierCellsTargeted     = []
        (sx,sy)                   = self.startPos # shorthand
        
        # determine whether we're done exploring
        self._determineDoneExploring()
        
        while True:
            if self.firstIteration:
                # this is my first iteration: put robot 0 in the start position
                
                mr_idx                = 0
                (mx_next,my_next)     = self.startPos
                self.firstIteration   = False
            
            else:
                # I already have robots in the area
                
                # identify all frontierCells
                frontierCells = []
                for (x,y) in self.allCellsIdx:
                    # don't consider the same call twice
                    if (x,y) in frontierCellsTargeted:
                        continue
                    # consider only open cells
                    if self.discoMap[x][y]!=1:
                        continue
                    # check wether this cell has unexplored neighbor cells
                    for (nx,ny) in self._OneHopNeighborhood(x,y):
                        if self.discoMap[nx][ny]==-1:
                            frontierCells += [((x,y),self._distance((sx,sy),(x,y)))]
                            break
                
                # keep only frontierCells with lowest rank
                frontierCells = [
                    fc[0] for fc in frontierCells
                    if fc[1]==sorted(frontierCells, key=lambda item: item[1])[0][1]
                ]
                
                # pick move robot (mv) and frontier cell (fc) to move towards
                #   Rules (most important first):
                #     - robot as close as possible to frontier
                #     - robot as close as possible to start position
                #     - frontier cell with many neighbors with a higher rank (avoids cutting corners)
                #     - frontier cell with many unexplored neighbors
                mr_idx                          = None
                fc_pos                          = None
                mr_distToStart                  = None
                mr_distToFc                     = None
                for (ridx,(rx,ry)) in enumerate(robotPositions):
                    
                    # don't move the same robot twice
                    if ridx in robotsMoved:
                        continue
                    
                    rDistToStart                = self._distance((sx,sy),(rx,ry))
                    max_numHigherRankNeighbors  = None
                    max_numUnexploredNeighbors  = None
                    for (fx,fy) in frontierCells:
                        rDistToFc               = self._distance((fx,fy),(rx,ry))
                        numHigherRankNeighbors  = self._numHigherRankNeighbors(fx,fy,self.discoMap)
                        numUnexploredNeighbors  = self._numUnexploredNeighbors(fx,fy,self.discoMap)
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
                (fx,fy)                = fc_pos                 # shorthand
                (mx_cur, my_cur)       = robotPositions[mr_idx] # shorthand
                (mx_next,my_next)      = (None,None)
                min_dist               = None
                for (x,y) in self._OneHopNeighborhood(mx_cur,my_cur):
                    if (
                        self.grid[x][y]==1              and
                        (x,y) not in robotPositions     and
                        (
                            min_dist==None or
                            self._distance((fx,fy),(x,y))<min_dist
                        )
                    ):
                        min_dist = self._distance((fx,fy),(x,y))
                        (mx_next,my_next) = (x,y)
                
                # abort if couldn't find a position to move to
                if mx_next==None:
                    break
                
                frontierCellsTargeted += [fc_pos]
            
            # move moveRobot
            robotPositions[mr_idx] = (mx_next,my_next)
            robotsMoved           += [mr_idx]
            
            # update the discoMap
            for (x,y) in self._OneHopNeighborhood(mx_next,my_next):
                if   self.grid[x][y] == 0:
                    self.discoMap[x][y]=0
                elif self.grid[x][y] == 1:
                    self.discoMap[x][y]=1
        
        return (robotPositions,self.discoMap,self.rankMaps[self.startPos])
    
    def _distance(self,pos1,pos2):
        
        # easy answer if same position
        if pos1==pos2:
            return 0
        
        # inverting pos1 and pos2 in case pos2 already cached (same distance)
        if (pos1 not in self.rankMaps) and (pos2 in self.rankMaps):
            temp = pos1
            pos1 = pos2
            pos2 = temp
        
        # shorthands
        (x1,y1) = pos1 
        (x2,y2) = pos2
        
        # if not in cache, compute rank map (and store in cache)
        if (x1,y1) not in self.rankMaps:
            
            # local variables
            shouldvisit               = []
            rankMap                   = []
            for row in self.grid:
                rankMap              += [[]]
                for col in row:
                    rankMap[-1]      += [None]

            # start from start position
            rankMap[x1][y1]           = 0
            shouldvisit              += [(x1,y1)]
            
            while True:
                
                # find cell to visit with lowest rank (abort if none)
                found         = False
                currentrank   = None
                for (x,y) in shouldvisit:
                    if  (
                            currentrank==None or
                            rankMap[x][y]<currentrank
                        ):
                        currentrank   = rankMap[x][y]
                        (cx,cy)       = (x,y)
                        found = True
                if found==False:
                    break
                
                # assign a height for all its neighbors
                for (nx,ny) in self._OneHopNeighborhood(cx,cy):
                    if rankMap[nx][ny] != None:
                        assert rankMap[nx][ny] <= currentrank+1 
                    if  (
                            self.grid[nx][ny]==1 and
                            rankMap[nx][ny] == None
                        ):
                        rankMap[nx][ny]     = currentrank+1
                        shouldvisit        += [(nx,ny)]
                
                # mark a visited
                shouldvisit.remove((cx,cy))
            
            self.rankMaps[(x1,y1)] = rankMap
        
        return self.rankMaps[(x1,y1)][x2][y2]
    
    def _numHigherRankNeighbors(self,x,y,discoMap):
        returnVal = 0
        rankMap = self.rankMaps[self.startPos] # shorthand
        for (nx,ny) in self._OneHopNeighborhood(x,y):
            if  (
                    discoMap[nx][ny]==1 and
                    rankMap[nx][ny]>rankMap[x][y]
                ):
                returnVal += 1
        return returnVal
    
    def _numUnexploredNeighbors(self,x,y,discoMap):
        returnVal = 0
        for (nx,ny) in self._OneHopNeighborhood(x,y):
            if discoMap[nx][ny]==-1:
                returnVal += 1
        return returnVal

#======== core simulator

'''
calculates steps taken from source to destination
'''

def singleExploration(grid,startPos,NavAlgClass,numRobots):
    navAlg         = NavAlgClass(grid,startPos,numRobots)
    robotPositions = [startPos]*numRobots
    kpis           = {
        'navAlg':    NavAlgClass.__name__,
        'numTicks':  0,
        'numSteps':  0,
    }
    
    while True:
        
        # think
        try:
            (nextRobotPositions,discoMap,rankMapStart)   = navAlg.think(robotPositions)
        except MappingDoneSuccess:
            break
        
        # move
        for (i,(nx,ny)) in enumerate(nextRobotPositions):
            (cx,cy) = robotPositions[i]
            if (nx,ny)!= (cx,cy):
                kpis['numSteps'] += 1
            robotPositions[i] = nextRobotPositions[i]
        
        # update KPIs
        kpis['numTicks'] += 1
        
        # print
        printGrid(discoMap,startPos,robotPositions,kpis)#,rankMapStart)
        
        #input()
    
    return kpis

#============================ main ============================================

def main():

    numRobots      = 10
    NavAlgClasses  = [
        NavigationRama,
        #NavigationRandomWalk,
        #NavigationBallistic,
    ]
    kpis           = []

    # create a scenario
    (grid,startPos) = genGrid()
    
    # execute the simulation for each navigation algorithm
    for NavAlgClass in NavAlgClasses:
        
        # run single run
        kpis_run   = singleExploration(grid,startPos,NavAlgClass,numRobots)
        
        # collect KPIs
        kpis      += [kpis_run]

    print(kpis)
    print('Done.')

if __name__=='__main__':
    main()
    #cProfile.run('main()')
