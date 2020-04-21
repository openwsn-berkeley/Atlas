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

GRID_SIZE          = 10
OBSTACLE_DENSITY   = 0.5

ALL_INDEXES        = []
for x in range(GRID_SIZE):
    for y in range(GRID_SIZE):
        ALL_INDEXES       += [(x,y)]

#============================ helper functions ================================

def genGrid():
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1],
        [0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
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
                line += ['?']
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

class Navigation(object):
    pass

class NavigationRandomWalk(Navigation):
    def __init__(self,grid,start):
        
        # store params
        self.grid            = grid
        self.start           = start
        
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
        for (rx,ry) in robotPositions:
            
            # explore your neighborhood
            validNextPosition = []
            
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
                    validNextPosition += [(nx,ny)]
            
            # move robot to randomly chosen valid neighbor
            if validNextPosition:
                nextRobotPositions += [random.choice(validNextPosition)]
            else:
                nextRobotPositions += [(rx,ry)]
        
        return (nextRobotPositions,self.discoMap)

#======== core simulator

'''
calculates steps taken from source to destination
'''
def singleRun(grid,start,NavAlgClass,numRobots):
    navAlg         = NavAlgClass(grid,start)
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
    numRobots      = 5
    NavAlgClasses  = [
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
