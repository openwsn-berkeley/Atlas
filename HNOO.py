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

def fixedGrid():
        grid = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
                [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 0, 0, 0, 0, 1, 1, 1],
                [0, 1, 1, 0, 0, 0, 0, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
            
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
            #elif (row,col)==target:
                #line += ['T']
            else:
                for r in robotPositions:
                    (rx,ry)= r
                    if (row,col) == (rx,ry):
                        line += ['R']
                    else:
                        line += ['']
                #else:
                    #if heights[row][col]==None:
                       # line += ['.']
                   # else:
                       # line += [str(heights[row][col]%10)]
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
        
        #abort id start = target
        if start == target:
            returnVal = False
            break
            
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
    
        def __str__(self):  
            return "parent: %s position: %s g: %s h %s f: %s \n" % (self.parent,self.position,self.g,self.h,self.f)
            
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
            # double check that node isnt in closed list already before adding it
            if current_node not in closed_list:
                closed_list     += [current_node]
            else:
                continue
                
            # abort if we found the goal
            if current_node == end_node: 
                self.directPath = []
                while current_node is not None:
                    self.directPath   += [current_node.position]
                    current_node       = current_node.parent
                self.directPath.reverse()
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

                # add node to neighbor nodes
                neighbor_nodes += [self.Node(parent=current_node, position=(nx,ny))]
              
            # loop through neighbor_nodes
            for n in neighbor_nodes:

                # don't explore child already visited
                for c in closed_list:
                    if n.position==c.position:
                        continue

                # create the f, g, and h values
                n.g  = current_node.g + 1
                n.h  = ((n.position[0] - end_node.position[0]) ** 2) + ((n.position[1] - end_node.position[1]) ** 2)
                n.f  = n.g + n.h
                
                # don't add node to open list if it is already there and has the same parent node
                for o in open_list:
                    if n.position == o.position and n.g > o.g:
                        continue

                # add the neighbor to the open list
                open_list += [n]
  
    def move(self,x,y):
        for i in range(len(self.directPath)-1):
            if self.directPath[i]==(x,y):
                return self.directPath[(i+1)]

class NavigationBallistic(Navigation):
    def __init__(self,grid,start):
        self.grid = grid
        self.start = start
        self.exploreMap =[[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
                       [-1, -1, -1, -1, -1, -1, -1, -1, -1,-1],
                       [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
                       [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
                       [-1, -1, -1, -1, -1, -1, -1, -1, -1,-1],
                       [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
                       [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
                       [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
                       [-1, -1, -1, -1, -1, -1, -1, -1, -1,-1],
                       [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]]
                       
        self.robotNum = 5
        #initiate positions of all robots as the enter one by one into grid


    def think(self, robotPositions)  :
        robotNextMoves = []
        numRows     = len(self.grid)
        numCols     = len(self.grid[0])
        for r in range(self.robotNum):
            (x,y) = robotPositions[r]
            # filter valid neighbors
            validNeighbors = []
            for (nx,ny) in [
                    (x-1,y-1),(x-1,y  ),(x-1,y+1),
                    (x  ,y-1),          (x  ,y+1),
                    (x+1,y-1),(x+1,y  ),(x+1,y+1),
                ]:
                if  (
                        (nx>=0)                and
                        (nx<numCols-1)         and
                        (ny>=0)                and
                        (ny<(numRows-1))       and
                        (self.grid[nx][ny]==1) and
                        (nx,ny) not in robotPositions
                    ):
                    validNeighbors += [(nx,ny)]
            # move to a randomly chosen valid neighbor
            #if self.grid[x-1][y] == 1:
            #    (x,y) = (x-1,y)    
            #else: 
            (x,y) = random.choice(validNeighbors)       
            robotNextMoves += [(x,y)] 
                                   
        print("robot planned next moves", robotNextMoves)
        return robotNextMoves 
    
    def move(self,robotNextMoves):
        robotPositions = []
        for r in range(self.robotNum):
            robotPositions += [robotNextMoves[r]]            
        print("robot move to:", robotPositions)
        return robotPositions   
        
    def mapping(self, robotPositions):
            
        for r in robotPositions:
            (rx,ry) = r
            for (rx,ry) in [
                (rx-1,ry-1),(rx-1,ry  ),(rx-1,ry+1),
                (rx  ,ry-1),          (rx  ,ry+1),
                (rx+1,ry-1),(rx+1,ry  ),(rx+1,ry+1),
            ]:
                if  self.grid[rx][ry] == 0:
                    self.exploreMap[rx][ry]=0
                elif self.grid[rx][ry] == 1:
                    self.exploreMap[rx][ry]=1
        return self.exploreMap

#======== core simulator

'''
calculates steps taken from source to destination
'''
def singleRun(grid,start,NavAlgClass):
    navAlg      = NavAlgClass(grid,start)
    path        = []
    (x,y)       = start
    robotPositions = [start, start, start, start, start]
    while True:
        # add to path
        path   += [(x,y)]
        
        #think
        robotNextMoves = navAlg.think(robotPositions)
        
        # move
        robotPositions   = navAlg.move(robotNextMoves)
        
        # plot
        exploredMap = navAlg.mapping(robotPositions)
        printGrid(exploredMap,start,robotPositions)
        
        # abort if map fully explored
        if -1 in exploredMap:
            break
    return len(path)

#============================ main ============================================

'''
asks user for the navigation algorithm they want to run then runs the specific function for it and returns the steps taken from start node to destination
'''
def main():
    numScenarios              = 1
    NavAlgClasses             = [
        #NavigationAstar,
        #NavigationRandomWalk,
        NavigationBallistic,
    ]
    
    # run all simulations
    numScenariosRun = 0
    with open('HNOO.log','w') as f:
        while True:
            
            # create a scenario
            grid        = fixedGrid()
            #start       = (random.randint(0,GRID_SIZE-1),random.randint(0,GRID_SIZE-1))
            # if I get here, this is a valid scenario
            start = (5,9)
            numScenariosRun += 1
            
            # execute the simulation for each navigation algorithm
            for NavAlgClass in NavAlgClasses:
                # run  single run
                steps   = singleRun(grid,start,NavAlgClass)
                
                # log the results
                f.write(json.dumps(
                    {
                        'grid':     grid,
                        'start':    start,
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
