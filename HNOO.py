'''
simulation of online and offline navigation algorithms

user has option to either give a specific grid through a config file, or to have the simulator generate a random grid :
'''

import json
import random
import math
import matplotlib.pyplot as plt
import numpy as np
#==============================================================================

#============================ helper functions ================================
'''
generate grid with given rows x coloums and randon obstacles
'''
def genRandGrid(rows,cols):
    print(rows, cols)
    randGrid=np.random.randint(2, size=(rows, cols))
    randGrid[5][5]=1
    print(randGrid)
    return randGrid
    

'''
performs online obstacle avoidance and returns the path found 
'''  
def ObstacleAvoidAlg(start, target,grid):
    gridSize=grid.shape
    currentNode = start
    onlinePath = [start]
    deadEnd=[]
    while (currentNode != target):
        x=currentNode[0]
        y=currentNode[1]
        neighbourNodes = [(x+1,y),(x+1,y+1),(x,y+1),(x-1,y+1),(x-1,y),(x-1,y-1),(x,y-1),(x+1,y-1)]
        avaliableNext=[]
        #print(neighbourNodes)
        for node in neighbourNodes:
            NN=node
           
            if (NN[0])>=0 and (NN[1])>=0 and NN[0]<(gridSize[0]-1) and NN[1]<(gridSize[1]-1) and (grid[NN[0]][NN[1]])== 1:
                if((node in onlinePath) == False):
                    avaliableNext.append(node)        
                    
        if avaliableNext==[]:
            print("no path avaliable")
            return avaliableNext
        else:
            moveTo = avaliableNext[random.randint(0,len(avaliableNext)-1)]
            onlinePath.append(moveTo)
            #print("online path so far is ", onlinePath)
            currentNode=moveTo

 
    
    print("Online path:",onlinePath)
    return onlinePath


'''
performs A* algorithm to find shortest path from start to target
'''

class Node():
    """A node class for A* Pathfinding"""

    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position

        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.position == other.position


def Astar(start, target, grid):
    """Returns a list of tuples as a path from the given start to the given end in the given maze"""

    # Create start and end node
    start_node = Node(None, start)
    start_node.g = start_node.h = start_node.f = 0
    end_node = Node(None, target)
    end_node.g = end_node.h = end_node.f = 0

    # Initialize both open and closed list
    open_list = []
    closed_list = []

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
      


'''
calculates steps taken from source to destination
'''
def singleRun(grid,obstacle,start,target,navAlg,runRun):
     
    if navAlg == 1:
        steps=len(Astar(start,target,grid))
    elif navAlg == 2:
        steps=len(ObstacleAvoidAlg(start,target,grid))
    return steps

#============================ main ============================================

'''
asks user for the navigation algorithm they want to run then runs the specific function for it and returns the steps taken from start node to destination
'''
def main():
    grids      = [genRandGrid(10,10)] 
    obstacles  = ['foo']     # FIXME [for now the grid is generated with random obstacles]
    starts     = [(0,0)]     
    targets    = [(5,5)]     
    numRuns    = 10
    navAlgs     = [2,1]             


    # run all simulations
    with open('HNOO.log','w') as f:
        for grid in grids:
            for obstacle in obstacles:
                for start in starts:
                    for target in targets:
                        for navAlg in navAlgs:
                            for runRun in range(numRuns):
   
                                # run  single run
                                steps = singleRun(grid,obstacle,start,target,navAlg,runRun)
                                
                                # log the results
                                f.write(json.dumps(
                                    {
                                        #'grid':     grid,
                                        'obstacle': obstacle,
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
    '''
    plt.xlabel('Smarts')
    plt.ylabel('Probability')
    plt.title('Histogram of IQ')
    plt.text(60, .025, r'$\mu=100,\ \sigma=15$')
    plt.xlim(40, 160)
    plt.ylim(0, 0.03)
    plt.grid(True)
    '''
    plt.show()
    plt.savefig('HNOO.png')
    
    
    print('Done.')
    
if __name__=='__main__':
    main()
    
