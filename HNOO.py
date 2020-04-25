'''
simulation of online and offline navigation algorithms
user has option to either give a specific grid through a config file, or to have the simulator generate a random grid :
'''

import os
import time
import json
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
    '''
    rows  = 20
    cols  = 30
    grid  = []
    for row in range(rows):
        thisRow = []
        for col in range(cols):
            if random.random()<0.00:
                thisRow += [0]
            else:
                thisRow += [1]
        grid += [thisRow]
    start = (int(rows/2),int(cols/2))
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
    start = (10,20)
    return (grid,start)

def printGrid(grid,start,robotPositions,rank=None):
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
                if (row,col)==start:
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
                # rank
                '''
                if rank:
                    line += [str(rank[row][col]%10)]
                    break
                '''
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
    def __init__(self,grid,start,numRobots):
        
        # store params
        self.grid            = grid
        self.start           = start
        self.numRobots       = numRobots
        
        # local variablels
        self.numRows         = len(self.grid)    # shorthand
        self.numCols         = len(self.grid[0]) # shorthand
        self.firstIteration  = True
        self.rankMap         = None
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
        
        return (nextRobotPositions,self.discoMap)
    
    def _pickNextPosition(self,ridx,rx,ry,validNextPositions):
        raise SystemError()
    
class NavigationRandomWalk(NavigationDistributed):
    
    def _pickNextPosition(self,ridx,rx,ry,validNextPositions):
        return random.choice(validNextPositions)

class NavigationBallistic(NavigationDistributed):

    def __init__(self,grid,start,numRobots):
        NavigationDistributed.__init__(self,grid,start,numRobots)
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
        (sx,sy)              = self.start # shorthand
        
        # determine whether we're done exploring
        self._determineDoneExploring()
        
        
        if self.firstIteration:
            moveBot               = 0
            (fx,fy)               = self.start
            self.firstIteration   = False
        
        else:
            # identify cells at the frontier
            frontierCells = []
            for (x,y) in self.allCellsIdx:
                # consider only open cells
                if self.discoMap[x][y]!=1:
                    continue
                # check wether this cell has unexplored neighbor cells
                isFrontierCell = False
                for (nx,ny) in self._OneHopNeighborhood(x,y):
                    if self.discoMap[nx][ny]==-1:
                        isFrontierCell = True
                        break
                if isFrontierCell==True:
                    frontierCells += [((x,y),self.rankMap[x][y])]
            
            # pick the frontierCell with lowest rank
            (fx,fy) = sorted(frontierCells, key=lambda item: item[1])[0][0]
            
            # pick a moveRobot
            distanceToStart = {}
            for (i,(x,y)) in enumerate(robotPositions):
                distanceToStart[i] = self.rankMap[x][y]
            moveBot = sorted(distanceToStart.items(), key=lambda item: item[1])[0][0]
        
        # move moveRobot to frontierCell
        nextRobotPositions[moveBot] = (fx,fy)
        
        # update the discoMap
        for (x,y) in self._OneHopNeighborhood(fx,fy):
            if   self.grid[x][y] == 0:
                self.discoMap[x][y]=0
            elif self.grid[x][y] == 1:
                self.discoMap[x][y]=1
        
        # compute ranks
        self.rankMap     = self.computeRankMap(self.grid,self.start)
        
        return (nextRobotPositions,self.discoMap,self.rankMap)
    
    def computeRankMap(self,grid,start):
        
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
        (sx,sy)                   = start
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

def singleRun(grid,start,NavAlgClass,numRobots):
    navAlg         = NavAlgClass(grid,start,numRobots)
    robotPositions = [start]*numRobots
    while True:
        
        # think
        try:
            (nextRobotPositions,discoMap,rankMap)   = navAlg.think(robotPositions)
        except MappingDoneSuccess:
            break
        
        # move
        robotPositions                      = nextRobotPositions
        
        # print
        printGrid(discoMap,start,robotPositions,rankMap)
        
        #input()
        #time.sleep(0.500)

#============================ main ============================================

def main():

    numRobots      = 10
    NavAlgClasses  = [
        NavigationRama,
        #NavigationRandomWalk,
        #NavigationBallistic,
    ]
    
    with open('HNOO.log','w') as f:
        
        # create a scenario
        (grid,start) = genGrid()
        
        # execute the simulation for each navigation algorithm
        for NavAlgClass in NavAlgClasses:
            # run  single run
            kpis    = singleRun(grid,start,NavAlgClass,numRobots)
    
    print('Done.')

if __name__=='__main__':
    main()
