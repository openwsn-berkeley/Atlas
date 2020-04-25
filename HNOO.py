'''
simulation of navigation algorithms for micro-robots
'''

import os
import random

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
    rows  = 5
    cols  = 5
    grid  = []
    for row in range(rows):
        thisRow = []
        for col in range(cols):
            if random.random()<0.00:
                thisRow += [0]
            else:
                thisRow += [1]
        grid += [thisRow]
    startPos = (int(rows/2),int(cols/2))
    '''
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
       #[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
       #[0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
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

def printGrid(grid,startPos,robotPositions,rank=None):
    output  = []
    output += ['']
    for row in range(len(grid)):
        line = []
        for col in range(len(grid[row])):
            while True:
                # robot
                robotFound = False
                for (rx,ry) in robotPositions:
                    if (row,col) == (rx,ry):
                        robotFound = True
                        line += ['*']
                        break
                if robotFound:
                    break
                # start position
                if (row,col)==startPos:
                    line += ['S']
                    break
                # wall
                if  grid[row][col]==0:
                    line += ['#']
                    break
                # unexplored
                if grid[row][col]==-1:
                    line += ['.']
                    break
                #'''
                # rank
                if rank:
                    line += [str(rank[row][col]%10)]
                    break
                #'''
                # explored
                line += [' ']
                break
        output += [' '.join(line)]
    output += ['']
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
        self.rankMapStart    = None
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
                    (nx<0)         or
                    (nx>=self.numRows)  or
                    (ny<0)         or
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
        
        return (nextRobotPositions,self.discoMap,self.rankMapStart)
    
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
        
        # local variables
        robotsMoved          = []
        nextRobotPositions   = robotPositions[:]
        (sx,sy)              = self.startPos # shorthand
        
        # determine whether we're done exploring
        self._determineDoneExploring()
        
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
                # consider only open cells
                if self.discoMap[x][y]!=1:
                    continue
                # check wether this cell has unexplored neighbor cells
                for (nx,ny) in self._OneHopNeighborhood(x,y):
                    if self.discoMap[nx][ny]==-1:
                        frontierCells += [((x,y),self.rankMapStart[x][y])]
                        break
            
            # keep only frontierCells with lowest rank
            frontierCells = [
                fc[0] for fc in frontierCells
                if fc[1]==sorted(frontierCells, key=lambda item: item[1])[0][1]
            ]
            
            # find the distance from each frontier cell to each robot
            rankMapFcs = {}
            for (fx,fy) in frontierCells:
                rankMapFcs[(fx,fy)] = self._computeRankMap(self.grid,fx,fy)
            
            # pick move robot (mv) and target frontier cell (fc)
            # Rules (most important first):
            # - robot as close as possible to frontier
            # - robot as close as possible to start
            mr_idx           = None
            mr_distToStart   = None
            mr_distToFc      = None
            fc_pos           = None
            fc_rankMap       = None
            for (ridx,(rx,ry)) in enumerate(nextRobotPositions):
                rDistToStart = self.rankMapStart[rx][ry]
                for ((fx,fy),rankMap) in rankMapFcs.items():
                    rDistToFc = rankMap[rx][ry]
                    if  (
                            mr_idx==None or
                            rDistToFc<mr_distToFc or
                            (
                                rDistToFc==mr_distToFc and
                                rDistToStart<mr_distToStart
                            )
                        ):
                        mr_idx         = ridx
                        mr_distToStart = rDistToStart
                        mr_distToFc    = rDistToFc
                        fc_pos         = (fx,fy)
                        fc_rankMap     = rankMap
            assert(mr_idx!=None)
            
            # pick new position for move robot
            (mx_cur, my_cur)       = nextRobotPositions[mr_idx] # shorthand
            (mx_next,my_next)      = (None,None)
            min_dist               = None
            for (x,y) in self._OneHopNeighborhood(mx_cur,my_cur):
                if (
                    self.grid[x][y]==1              and
                    (x,y) not in nextRobotPositions and
                    (
                        min_dist==None or
                        fc_rankMap[x][y]<min_dist
                    )
                ):
                    min_dist = fc_rankMap[x][y]
                    (mx_next,my_next) = (x,y)
            assert(mx_next!=None)
            assert(my_next!=None)
        
        # move moveRobot
        nextRobotPositions[mr_idx] = (mx_next,my_next)
        
        # update the discoMap
        for (x,y) in self._OneHopNeighborhood(mx_next,my_next):
            if   self.grid[x][y] == 0:
                self.discoMap[x][y]=0
            elif self.grid[x][y] == 1:
                self.discoMap[x][y]=1
        
        # compute ranks
        self.rankMapStart = self._computeRankMap(self.grid,sx,sy)
        
        return (nextRobotPositions,self.discoMap,self.rankMapStart)
    
    def _computeRankMap(self,grid,sx,sy):
        
        # local variables
        rankMap                   = []
        shouldvisit               = []
        for row in grid:
            rankMap              += [[]]
            shouldvisit          += [[]]
            for col in row:
                rankMap[-1]      += [None]
                shouldvisit[-1]  += [False]

        # start from start position
        rankMap[sx][sy]           = 0
        shouldvisit[sx][sy]       = True
        
        while True:
            
            # find cell to visit with lowest rank (abort if none)
            found         = False
            currentrank   = None
            for (x,y) in self.allCellsIdx:
                if  (
                        shouldvisit[x][y]==True and
                        (
                            currentrank==None or
                            rankMap[x][y]<currentrank
                        )
                    ):
                    currentrank   = rankMap[x][y]
                    (cx,cy)       = (x,y)
                    found = True
            if found==False:
                break
            
            # assign a height for all its neighbors
            for (nx,ny) in self._OneHopNeighborhood(cx,cy):
                if (
                        grid[nx][ny]==1 and
                        (
                            rankMap[nx][ny] == None or
                            rankMap[nx][ny]>currentrank+1
                        )
                    ):
                    rankMap[nx][ny]     = currentrank+1
                    shouldvisit[nx][ny] = True
            
            # mark a visited
            shouldvisit[cx][cy] = False
        
        return rankMap

#======== core simulator

'''
calculates steps taken from source to destination
'''

def singleExploration(grid,startPos,NavAlgClass,numRobots):
    navAlg         = NavAlgClass(grid,startPos,numRobots)
    robotPositions = [startPos]*numRobots
    numTicks       = 0
    numSteps       = 0
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
                numSteps += 1
            robotPositions[i] = nextRobotPositions[i]
        
        # print
        printGrid(discoMap,startPos,robotPositions,rankMapStart)
        
        # update KPIs
        numTicks += 1
        
        #input()
    
    return {
        'numTicks': numTicks,
        'numSteps': numSteps,
    }

#============================ main ============================================

def main():

    numRobots      = 3
    NavAlgClasses  = [
        NavigationRama,
        NavigationRandomWalk,
        NavigationBallistic,
    ]
    kpis           = {}

    # create a scenario
    (grid,startPos) = genGrid()
    
    # execute the simulation for each navigation algorithm
    for NavAlgClass in NavAlgClasses:
        
        # run single run
        kpis_run   = singleExploration(grid,startPos,NavAlgClass,numRobots)
        
        # collect KPIs
        kpis[NavAlgClass.__name__]=kpis_run

    print(kpis)
    print('Done.')

if __name__=='__main__':
    main()
