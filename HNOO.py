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

def euclidian(pos1,pos2):
    (x1,y1) = pos1 # shorthand
    (x2,y2) = pos2 # shorthand
    return math.sqrt((x1-x2)**2 + (y1-y2)**2)

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

class Navigation(object):
    def __init__(self,grid,start,numRobots):
        
        # store params
        self.grid            = grid
        self.start           = start
        self.numRobots       = numRobots
        
        # local variablels
        self.numRows         = len(self.grid)    # shorthand
        self.numCols         = len(self.grid[0]) # shorthand
        
        # local variables
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
            raise ExceptionFullDiscoMap
    
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
        nextRobotPositions   = robotPositions[:]
        
        # determine whether we're done exploring
        self._determineDoneExploring()
        
        # identify robots at the frontier
        frontierBots = []
        for (ridx,(rx,ry)) in enumerate(robotPositions):
            # check that robot has frontier it its 2-neighborhood
            closeToFrontier = False
            for (nx,ny) in self._TwoHopNeighborhood(rx,ry):
                if self.discoMap[nx][ny]==-1:
                    closeToFrontier = True
                    break
            if closeToFrontier==False:
                continue
            # check that robot has open space in its 1-neighborhood that's further than itself
            for (nx,ny) in self._OneHopNeighborhood(rx,ry):
                if (
                    self.grid[nx][ny]==1            and  # open position (not wall)
                    ((nx,ny) not in robotPositions) and  # no robot there
                    (nx,ny)!=self.start             and  # not the start position
                    euclidian(self.start,(nx,ny))>euclidian(self.start,(rx,ry))
                ):
                    frontierBots += [ridx]
                    break
        
        # pick a frontierBot
        distanceToStart = {}
        (sx,sy) = self.start # shorthand
        for (ridx,(x,y)) in enumerate(robotPositions):
            if ridx not in frontierBots:
                continue
            distanceToStart[ridx] = euclidian((sx,sy),(x,y))
        frontierBot = sorted(distanceToStart.items(), key=lambda item: item[1])[0][0]
        
        # pick a cell for a new Robot
        (fx,fy) = robotPositions[frontierBot]
        while True:
            (rx,ry) = random.choice(self._OneHopNeighborhood(fx,fy))
            if  (
                    self.grid[rx][ry]==1 and
                    ((rx,ry) not in robotPositions) and
                    (rx,ry)!=self.start
                ):
                break
        
        # pick a robot to move and change its position
        distanceToStart = {}
        (sx,sy) = self.start # shorthand
        for (ridx,(x,y)) in enumerate(robotPositions):
            distanceToStart[ridx] = math.sqrt((x-sx)**2 + (y-sy)**2)
        newBot = sorted(distanceToStart.items(), key=lambda item: item[1])[0][0]
        nextRobotPositions[newBot] = (rx,ry)
        
        # update the discoMap
        for (nx,ny) in self._OneHopNeighborhood(rx,ry):
            if   self.grid[nx][ny] == 0:
                self.discoMap[nx][ny]=0
            elif self.grid[nx][ny] == 1:
                self.discoMap[nx][ny]=1
        
        return (nextRobotPositions,self.discoMap)

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

    numRobots      = 100
    NavAlgClasses  = [
        NavigationRama,
        #NavigationBallistic,
        #NavigationRandomWalk,
    ]
    
    with open('HNOO.log','w') as f:
        
        # create a scenario
        grid        = genGrid()
        start       = (10,10)
        
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
