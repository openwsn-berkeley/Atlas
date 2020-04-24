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

OBSTACLE_DENSITY   = 0.5

#============================ helper functions ================================

def genGrid():
    '''
    rows = 10
    cols = 12
    returnVal = []
    for row in range(rows):
        thisRow = []
        for col in range(cols):
            if random.random()<OBSTACLE_DENSITY:
                thisRow += [0]
            else:
                thisRow += [1]
        returnVal += [thisRow]
    return returnVal
    '''
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    return grid
        
def printGrid(grid,start,robotPositions):
    output  = []
    output += ['']
    for row in range(len(grid)):
        line = []
        for col in range(len(grid[row])):
            if   grid[row][col]==0:
                line += ['#']
            elif (row,col)==start:
                line += ['S']
            elif grid[row][col]==-1:
                line += ['.']
            else:
                robotFound = False
                for (rx,ry) in robotPositions:
                    if (row,col) == (rx,ry):
                        robotFound = True
                        line += ['R']
                        break
                if not robotFound:
                    line += [' ']
        output += [' '.join(line)]
    output += ['']
    output = '\n'.join(output)
    os.system('cls')
    print(output)
    time.sleep(0.010)

#============================ classes =========================================

#======== exceptions

class ExceptionFullDiscoMap(Exception):
    pass

#======== navigation algorithms

class NavigationDistributed(object):
    def __init__(self,grid,start,numRobots):
        
        # store params
        self.grid            = grid
        self.start           = start
        self.numRobots       = numRobots
        
        # local variables
        self.discoMap        = []
        for row in grid:
            self.discoMap   += [[]]
            for col in row:
                self.discoMap[-1] += [-1]

    def think(self, robotPositions):

        # shorthand
        numRows              = len(self.grid)
        numCols              = len(self.grid[0])
        
        # returnVal
        nextRobotPositions   = []
        
        # determine whether we're done exploring
        fullDiscoMap = True
        for row in self.discoMap:
            for cell in row:
                if cell == -1:
                    fullDiscoMap = False
                    break
        if fullDiscoMap:
            raise ExceptionFullDiscoMap
        
        # move each robot
        for (ridx,(rx,ry)) in enumerate(robotPositions):
            
            # explore your neighborhood
            validNextPositions = []
            
            for (nx,ny) in [
                    (rx-1,ry-1),(rx-1,ry  ),(rx-1,ry+1),
                    (rx  ,ry-1),            (rx  ,ry+1),
                    (rx+1,ry-1),(rx+1,ry  ),(rx+1,ry+1),
                ]:
                
                # do not consider cells outside the grid
                if  (
                        (nx<0)         or
                        (nx>=numRows)  or
                        (ny<0)         or
                        (ny>=numCols)
                    ):
                    continue
                
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
            (nextRobotPositions,discoMap)   = navAlg.think(robotPositions)
        except ExceptionFullDiscoMap:
            break
        
        # move
        robotPositions                      = nextRobotPositions
        
        # print
        printGrid(discoMap,start,robotPositions)


#============================ main ============================================

def main():

    numRobots      = 1
    NavAlgClasses  = [
        NavigationBallistic,
        NavigationRandomWalk,
    ]
    
    with open('HNOO.log','w') as f:
        
        # create a scenario
        grid        = genGrid()
        start       = (5,11)
        
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
