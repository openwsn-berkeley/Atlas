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

GRID_SIZE          = 30
OBSTACLE_DENSITY   = 0.5

ALL_INDEXES        = []
for x in range(GRID_SIZE):
    for y in range(GRID_SIZE):
        ALL_INDEXES       += [(x,y)]

#============================ helper functions ================================

'''
generate grid with given rows x coloums and randon obstacles.

    [
        [0,1,0,1,0,1],
        [0,1,0,1,0,1],
        [0,1,0,1,0,1],
        [0,1,0,1,0,1],
        [0,1,0,1,0,1],
    ]
'''
def genRandGrid(rows,cols):
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

def printGrid(grid,start,target,robotPosition=None,heights=None):
    output  = []
    output += ['']
    for row in range(len(grid)):
        line = []
        for col in range(len(grid[row])):
            if   grid[row][col]==0:
                line += ['#']
            elif (row,col)==start:
                line += ['S']
            elif (row,col)==target:
                line += ['T']
            else:
                if robotPosition:
                    if (row,col)==robotPosition:
                        line += ['R']
                    else:
                        line += ['.']
                else:
                    if heights[row][col]==None:
                        line += ['.']
                    else:
                        line += [str(heights[row][col]%10)]
        output += [' '.join(line)]
    output += ['']
    output = '\n'.join(output)
    os.system('cls')
    print(output)
    time.sleep(0.100)

def validateScenario(grid,start,target):
    returnVal = True
    
    numRows     = len(grid)
    numCols     = len(grid[0])
    
    while True:
        
        # abort if start position is a obstacle
        (x,y) = start
        if grid[x][y]==0:
            returnVal = False
            break
        
        # abort if target position is a obstacle
        (x,y) = target
        if grid[x][y]==0:
            returnVal = False
            break
        
        # abort if no path between start and target
        heights       = [[None  for x in range(numCols)] for y in range(numRows)]
        shouldvisit   = [[False for x in range(numCols)] for y in range(numRows)]
        # start from target
        (x,y) = target
        heights[x][y]     = 0
        shouldvisit[x][y] = True
        
        while True:
            
            # find cell to visit with lowest height (abort if none)
            found         = False
            currentheight = None
            for (x,y) in ALL_INDEXES:
                if  (
                        shouldvisit[x][y]==True and
                        (
                            currentheight==None or
                            heights[x][y]<currentheight
                        )
                    ):
                    currentheight = heights[x][y]
                    (cx,cy)       = (x,y)
                    found = True
            if found==False:
                break
            
            # assign a height for all its neighbors
            for (nx,ny) in [
                    (cx-1,cy-1),(cx-1,cy  ),(cx-1,cy+1),
                    (cx  ,cy-1),            (cx  ,cy+1),
                    (cx+1,cy-1),(cx+1,cy  ),(cx+1,cy+1),
                ]:
                if (
                    nx>=0           and
                    nx<=numCols-1   and
                    ny>=0           and
                    ny<=numRows-1   and
                    grid[nx][ny]==1 and
                    (
                        heights[nx][ny] == None or
                        heights[nx][ny]>currentheight+1
                    )
                ):
                    heights[nx][ny]     = currentheight+1
                    shouldvisit[nx][ny] = True
            
            # mark a visited
            shouldvisit[cx][cy] = False
            
        # abort if start cell doesn't have a height
        (x,y) = start
        if heights[x][y]==None:
            returnVal = False
            break
        
        # if you get here, it's a valid grid
        break
    
    return returnVal

#============================ classes =========================================

#======== navigation algorithms

class Navigation(object):
    pass

class NavigationRandomWalk(Navigation):
    def __init__(self,grid,start,target):
        self.grid = grid
    def move(self,x,y):
        numRows     = len(self.grid)
        numCols     = len(self.grid[0])
        
        # filter valid neighbors
        validNeighbors = []
        for (nx,ny) in [
                (x-1,y-1),(x-1,y  ),(x-1,y+1),
                (x  ,y-1),          (x  ,y+1),
                (x+1,y-1),(x+1,y  ),(x+1,y+1),
            ]:
            if  (
                    (nx>=0)             and
                    (nx<numCols-1)      and
                    (ny>=0)             and
                    (ny<(numRows-1))    and
                    (self.grid[nx][ny]==1)
                ):
                validNeighbors += [(nx,ny)]
        
        # make sure if no valid neighbors
        assert validNeighbors
        
        # move to a randomly chosen valid neighbor
        (x,y) = random.choice(validNeighbors)
        
        return (x,y)

class NavigationAstar(Navigation):
    
    class Node():
        """A node class for A* Pathfinding"""

        def __init__(self, parent=None, position=None):
            self.parent      = parent
            self.position    = position

            self.g           = 0
            self.h           = 0
            self.f           = 0

        def __eq__(self, other):
            return self.position == other.position
    
    def __init__(self,grid,start,target):
        self.grid            = grid
        self.directPath      = [] 
        
        # pre-compute shortest path, store in directPath
      
        # create start and end node
        numRows              = len(self.grid)
        numCols              = len(self.grid[0])
        start_node           = self.Node(parent=None, position=start)
        end_node             = self.Node(parent=None, position=target)
        # initialize both open and closed list
        open_list            = []
        closed_list          = []

        # Add the start node
        open_list           += [start_node]

        # Loop until you find the end
        while open_list:

            # get the current node
            current_index    = 0
            current_node     = open_list[current_index]
            for (index,open_node) in enumerate(open_list):
                if open_node.f < current_node.f:
                    current_node  = open_node
                    current_index = index

            # pop current off open list, add to closed list
            open_list.pop(current_index)
            closed_list     += [current_node]

            # abort if we found the goal
            if current_node == end_node:
                self.directPath = []
                while current_node is not None:
                    self.directPath   += [current_node.position]
                    current_node       = current_node.parent
                self.directPath.reverse()
                print("A* path:", self.directPath)
                break

            # add valid neighbor nodes
            neighbor_nodes = []
            (cx,cy)        = current_node.position
            for (nx,ny) in [
                    (cx-1, cy-1), (cx-1, cy), (cx-1, cy+1),
                    (  cx, cy-1),             ( cx,  cy+1),
                    (cx+1, cy-1), (cx+1, cy), (cx+1, cy+1),
                ]:

                # skip if ouside grid
                if  (
                        nx < 0             or
                        nx > (numRows - 1) or
                        ny < 0             or
                        ny > (numCols -1)
                    ):
                    continue

                # skip if obstacle
                if grid[nx][ny]!=1:
                    continue
                
                # add
                neighbor_nodes += [self.Node(parent=current_node, position=(nx,ny))]

            # loop through neighbor_nodes
            for n in neighbor_nodes:

                # don't explore child already visited
                for c in closed_list:
                    if n==c:
                        continue

                # create the f, g, and h values
                n.g  = current_node.g + 1
                n.h  = ((n.position[0] - end_node.position[0]) ** 2) + ((n.position[1] - end_node.position[1]) ** 2)
                n.f  = n.g + n.h

                # TBD
                for o in open_list:
                    if n == o and n.g > o.g:
                        continue

                # add the neighbor to the open list
                open_list += [n]
                
    def move(self,x,y):
        for i in range(len(self.directPath)-1):
            if self.directPath[i]==(x,y):
                return self.directPath[(i+1)]

#======== core simulator

'''
calculates steps taken from source to destination
'''
def singleRun(grid,start,target,NavAlgClass):
    navAlg      = NavAlgClass(grid,start,target)
    path        = []
    (x,y)       = start
    
    while True:
        # add to path
        path   += [(x,y)]
        
        # move
        (x,y)   = navAlg.move(x,y)
        
        # plot
        printGrid(grid,start,target,robotPosition=(x,y))
        
        # abort if you're at target
        if (x,y)==target:
            break
    
    return len(path)

#============================ main ============================================

'''
asks user for the navigation algorithm they want to run then runs the specific function for it and returns the steps taken from start node to destination
'''
def main():
    numScenarios              = 1
    NavAlgClasses             = [
        NavigationAstar,
        #NavigationRandomWalk,
    ]
    
    # run all simulations
    numScenariosRun = 0
    with open('HNOO.log','w') as f:
        while True:
            
            # create a scenario
            grid        = genRandGrid(GRID_SIZE,GRID_SIZE)
            start       = (random.randint(0,GRID_SIZE-1),random.randint(0,GRID_SIZE-1))
            target      = (random.randint(0,GRID_SIZE-1),random.randint(0,GRID_SIZE-1))
            
            # skip if not valid scenario
            if validateScenario(grid,start,target)==False:
                continue
            
            # if I get here, this is a valid scenario
            numScenariosRun += 1
            
            # execute the simulation for each navigation algorithm
            for NavAlgClass in NavAlgClasses:
                # run  single run
                steps   = singleRun(grid,start,target,NavAlgClass)
                
                # log the results
                f.write(json.dumps(
                    {
                        'grid':     grid,
                        'start':    start,
                        'target':   target,
                        'steps':    steps,
                    }
                )+'\n')
            
            # stop after numScenarios
            if numScenariosRun==numScenarios:
                break

    # analyze the results
    dist_steps = []
    with open('HNOO.log','r') as f:
        for line in f:
            results = json.loads(line)
            dist_steps += [results['steps']]
    plt.hist(dist_steps)
    plt.show()
    plt.savefig('HNOO.png')
    
    print('Done.')
    
if __name__=='__main__':
    main()
