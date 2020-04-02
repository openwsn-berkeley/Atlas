'''
simulation of online and offline navigation algorithms

user has option to either give a specific grid through a config file, or to have the simulator generate a random grid :
'''

import json
import random
import math
import matplotlib.pyplot as plt

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
            thisRow += [random.randint(0,1)]
        returnVal += [thisRow]
    return returnVal

def printGrid(grid,start,target,robotPosition):
    output  = []
    output += ['']
    for row in range(len(grid)):
        line = []
        for col in range(len(grid[row])):
            if   grid[row][col]==0:
                line += ['#']
            elif (row,col)==start:
                line += ['S']
            elif (row,col)==robotPosition:
                line += ['R']
            elif (row,col)==target:
                line += ['T']
            else:
                line += [' ']
        output += [' '.join(line)]
    output += ['']
    output = '\n'.join(output)
    print(output)

'''
performs online obstacle avoidance and returns the path found 
'''  
def ObstacleAvoidAlg(start, target, grid):
    numRows     = len(grid)
    numCols     = len(grid[0])
    path        = []
    (x,y)       = start
    
    while True:
        # add to path
        path   += [(x,y)]
        
        # filter valid neighbors
        validNeighbors = []
        for (nx,ny) in [
                (x-1,y-1),(x-1,y  ),(x-1,y+1),
                (x  ,y-1),          (x  ,y+1),
                (x+1,y-1),(x+1,y  ),(x+1,y+1),
            ]:
            if  (
                    (nx>=0)           and
                    (nx<numCols-1)    and
                    (ny>=0)           and
                    (ny<(numRows-1))  and
                    (grid[nx][ny]==1)
                ):
                validNeighbors += [(nx,ny)]
        
        # make sure if no valid neighbors
        assert validNeighbors
        
        # move to a randomly chosen valid neighbor
        (x,y) = random.choice(validNeighbors)
        
        # abort if you're at target
        if (x,y)==target:
            break
    
    return len(path)

'''
performs A* algorithm to find shortest path from start to target
'''
def Astar(start, target, grid):
    """Returns a list of tuples as a path from the given start to the given end in the given maze"""

    # Create start and end node
    start_node   = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node     = Node(None, target)
    end_node.g   = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list    = []
    closed_list  = []

    # Add the start node
    open_list.append(start_node)

    # Loop until you find the end
    while len(open_list) > 0:

        # Get the current node
        current_node = open_list[0]
        current_index = 0
        for index, item in enumerate(open_list):
            if item.f < current_node.f:
                current_node = item
                current_index = index

        # Pop current off open list, add to closed list
        open_list.pop(current_index)
        closed_list.append(current_node)

        # Found the goal
        if current_node == end_node:
            path = []
            current = current_node
            while current is not None:
                path.append(current.position)
                current = current.parent
            print("A* path: ", path[::-1] )
            return path[::-1] # Return reversed path

        # Generate children
        children = []
        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]: # Adjacent squares

            # Get node position
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

            # Make sure within range
            if node_position[0] > (grid.shape[0] - 1) or node_position[0] < 0 or node_position[1] > (grid.shape[1] -1) or node_position[1] < 0:
                continue

            # Make sure walkable terrain
            if grid[node_position[0]][node_position[1]] != 1:
                continue

            # Create new node
            new_node = Node(current_node, node_position)

            # Append
            children.append(new_node)

        # Loop through children
        for child in children:

            # Child is on the closed list
            for closed_child in closed_list:
                if child == closed_child:
                    continue

            # Create the f, g, and h values
            child.g = current_node.g + 1
            child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
            child.f = child.g + child.h

            # Child is already in the open list
            for open_node in open_list:
                if child == open_node and child.g > open_node.g:
                    continue

            # Add the child to the open list
            open_list.append(child)

class Node():
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None):
        self.parent     = parent
        self.position   = position

        self.g          = 0
        self.h          = 0
        self.f          = 0

    def __eq__(self, other):
        return self.position == other.position
        
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
    def __init__(self,grid,start,target):
        self.grid       = grid
        self.directPath = [] 
        
        # A* algorithm that computes shortest directPath
      
        # Create start and end node
        start_node   = Node(None, start)
        start_node.g = start_node.h = start_node.f = 0
        end_node     = Node(None, target)
        end_node.g   = end_node.h = end_node.f = 0
        numRows     = len(self.grid)
        numCols     = len(self.grid[0])
        # Initialize both open and closed list
        open_list    = []
        closed_list  = []

        # Add the start node
        open_list.append(start_node)

        # Loop until you find the end
        while len(open_list) > 0:

            # Get the current node
            current_node = open_list[0]
            current_index = 0
            for index, item in enumerate(open_list):
                if item.f < current_node.f:
                    current_node = item
                    current_index = index

            # Pop current off open list, add to closed list
            open_list.pop(current_index)
            closed_list.append(current_node)

            # Found the goal
            if current_node == end_node:
                path    = []
                current = current_node
                while current is not None:
                    path.append(current.position)
                    current = current.parent
                self.directPath = path[::-1]
                print("A* path:", self.directPath)
                break


            # Generate children
            children = []
            for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]: # Adjacent squares

                # Get node position
                node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])

                # Make sure within range
                if node_position[0] > (numRows - 1) or node_position[0] < 0 or node_position[1] > (numCols -1) or node_position[1] < 0:
                    continue

                # Make sure walkable terrain
                if grid[node_position[0]][node_position[1]] != 1:
                    continue

                # Create new node
                new_node = Node(current_node, node_position)

                # Append
                children.append(new_node)

            # Loop through children
            for child in children:

                # Child is on the closed list
                for closed_child in closed_list:
                    if child == closed_child:
                        continue

                # Create the f, g, and h values
                child.g = current_node.g + 1
                child.h = ((child.position[0] - end_node.position[0]) ** 2) + ((child.position[1] - end_node.position[1]) ** 2)
                child.f = child.g + child.h

                # Child is already in the open list
                for open_node in open_list:
                    if child == open_node and child.g > open_node.g:
                        continue

                # Add the child to the open list
                open_list.append(child)
                
    def move(self,x,y):
        for i in range(len(self.directPath)-1):
            if self.directPath[i]==(x,y):
                return self.directPath[(i+1)]

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
        printGrid(grid,start,target,(x,y))
        
        # abort if you're at target
        if (x,y)==target:
            break
    
    return len(path)

#============================ main ============================================

'''
asks user for the navigation algorithm they want to run then runs the specific function for it and returns the steps taken from start node to destination
'''
def main():
    grids         = [genRandGrid(10,10)] 
    starts        = [(0,0)]
    targets       = [(5,5)]
    NavAlgClasses = [
        NavigationRandomWalk,
        NavigationAstar,
    ]
    numRuns       = 2

    # run all simulations
    with open('HNOO.log','w') as f:
        for grid in grids:
            for start in starts:
                for target in targets:
                    for NavAlgClass in NavAlgClasses:
                        
                        for runRun in range(numRuns):

                            # run  single run
                            steps = singleRun(grid,start,target,NavAlgClass)
                            
                            # log the results
                            f.write(json.dumps(
                                {
                                    #'grid':     grid,
                                    'start':    start,
                                    'target':   target,
                                    'runRun':   runRun,
                                    'steps':    steps,
                                }
                            )+'\n')

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
    
