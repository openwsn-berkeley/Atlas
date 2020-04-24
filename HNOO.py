'''
simulation of online and offline navigation algorithms
user has option to either give a specific grid through a config file, or to have the simulator generate a random grid :
'''

import os
import time
import json
import random
import math
import itertools
import matplotlib.pyplot as plt

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
    start = (int(rows/2),int(cols/2))
    grid  = []
    for row in range(rows):
        thisRow = []
        for col in range(cols):
            if random.random()<0.00:
                thisRow += [0]
            else:
                thisRow += [1]
        grid += [thisRow]
    return (grid,start)
    '''
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
       #[0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
       #[0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
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
    '''
    return grid

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
                        line += ['R']
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
                if rank:
                    line += [str(rank[row][col]%10)]
                    break
                # explored
                line += [' ']
                break
        output += [' '.join(line)]
    output += ['']
    output = '\n'.join(output)
    os.system('cls')
    print(output)
    print(robotPositions)

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
        for row in grid:
            self.discoMap   += [[]]
            for col in row:
                self.discoMap[-1] += [-1]
    
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
            (mx,my)               = self.start
            self.firstIteration   = False
        
        else:
            # identify robots at the frontier
            frontierBots = []
            for (i,(x,y)) in enumerate(robotPositions):
                # check that robot has frontier it its 2-neighborhood
                closeToFrontier = False
                for (nx,ny) in self._TwoHopNeighborhood(x,y):
                    if self.discoMap[nx][ny]==-1:
                        closeToFrontier = True
                        break
                if closeToFrontier==False:
                    continue
                # check that robot has open space in its 1-neighborhood that's further than itself
                for (nx,ny) in self._OneHopNeighborhood(x,y):
                    if (
                        self.grid[nx][ny]==1            and  # open position (not wall)
                        ((nx,ny) not in robotPositions) and  # no robot there
                        (nx,ny)!=self.start             and  # not the start position
                        self.rankMap[nx][ny]>self.rankMap[x][y]
                    ):
                        frontierBots += [i]
                        break
            if not frontierBots:
                raise MappingDoneIncomplete
            
            # pick a frontierBot
            distanceToStart = {}
            for (i,(x,y)) in enumerate(robotPositions):
                if i not in frontierBots:
                    continue
                distanceToStart[i] = self.rankMap[x][y]
            frontierBot = sorted(distanceToStart.items(), key=lambda item: item[1])[0][0]
            
            # pick a moveRobot
            distanceToStart = {}
            for (i,(x,y)) in enumerate(robotPositions):
                distanceToStart[i] = math.sqrt((x-sx)**2 + (y-sy)**2)
            moveBot = sorted(distanceToStart.items(), key=lambda item: item[1])[0][0]
            
            # pick a cell for moveRobot
            (fx,fy) = robotPositions[frontierBot]
            while True:
                (mx,my) = random.choice(self._OneHopNeighborhood(fx,fy))
                if  (
                        self.grid[mx][my]==1            and
                        ((mx,my) not in robotPositions) and
                        (mx,my)!=self.start             and
                        self.rankMap[mx][my]>self.rankMap[fx][fy]
                    ):
                    break
        
        # move moveRobot
        nextRobotPositions[moveBot] = (mx,my)
        
        # update the discoMap
        for (nx,ny) in self._OneHopNeighborhood(mx,my):
            if   self.grid[nx][ny] == 0:
                self.discoMap[nx][ny]=0
            elif self.grid[nx][ny] == 1:
                self.discoMap[nx][ny]=1
        
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
        (sx,sy) = start
        rankMap[sx][sy]           = 0
        shouldvisit[sx][sy]       = True
        
        while True:
            
            # find cell to visit with lowest rank (abort if none)
            found         = False
            currentrank   = None
            for x in range(self.numRows):
                for y in range(self.numCols):
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
        
        input()
        #time.sleep(0.500)

#============================ main ============================================

def main():

    numRobots      = 1
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
            
            # log the results
            f.write(json.dumps(
                {
                    'grid':     grid,
                    'start':    start,
                    'kpis':     kpis,
                }
            )+'\n')
    
    # analyze the results
    # TODO
    
    print('Done.')

if __name__=='__main__':
    main()
