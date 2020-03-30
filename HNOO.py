'''
simulation of online and offline navigation algorithms

user has option to either give a specific grid through a config file, or to have the simulator generate a random grid :
'''

import json
import random
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
    print(randGrid)
    return randGrid
    
'''
gets pre-defined grids using dimentions
'''
def getGrid():
    grid1 = [[1,1,0,1,0,1,1,1,1,0],
            [1,0,1,0,0,1,0,0,1,0],
            [0,1,1,0,1,1,0,0,1,0],
            [1,1,1,1,0,1,0,0,1,1],
            [1,1,1,0,0,1,0,0,1,1],]
    print(grid1)
    return grid1
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

 
    
    print("Full Online path",onlinePath)
    return onlinePath


'''
performs A* algorithm to find shortest path from start to target
'''
def AstarAlgorithm(start, target,grid):
    
    currentNode = start
    astarPath = [start]
    gridSize=grid.shape
    
    while (currentNode != target):
        x=currentNode[0]
        y=currentNode[1]
        g=0
        neighbourNodes = [(x+1,y),(x+1,y+1),(x,y+1),(x-1,y+1),(x-1,y),(x-1,y-1),(x,y-1),(x+1,y-1)]
        childNodes=[]
        costF=[]
        #print(neighbourNodes)
        for node in neighbourNodes:
            #print("node = ", node)
            NN=node
            idx=neighbourNodes.index(node)
            if (NN[0])>=0 and (NN[1])>=0 and NN[0]<(gridSize[0]-1) and NN[1]<(gridSize[1]-1) and (grid[NN[0]][NN[1]])== 1:
                if(node != (0,0)) and (node in astarPath) == False:
                    #print("index =" , idx)
                    childNodes.append(node)
                    g=g+1
                    h=((currentNode[0]-target[0])**2 + (currentNode[1]-target[1])**2)
                    f=g+h
                    costF.append(node)
                    #print("costs", costF)
                    
        #print(childNodes)
        if childNodes==[]:
            print("no path avaliable")
            return childNodes
        else:
            minCost=min(costF)
            #print("minF = ", costF)
            #print(costF.index(minCost))
            moveTo = childNodes[costF.index(minCost)]
            #print(moveTo)
            astarPath.append(moveTo)
            #print("astarPath path so far is ", astarPath)
            currentNode=moveTo

           
    
    print("Full A* Path" , astarPath)
    return astarPath

'''
calculates steps taken from source to destination
'''
def singleRun(grid,obstacle,start,target,navAlg,runRun):
    
    if navAlg == 1:
        steps=len(AstarAlgorithm(start,target,grid))
    elif navAlg == 2:
        steps=len(ObstacleAvoidAlg(start,target,grid))
    return steps

#============================ main ============================================

'''
asks user for the navigation algorithm they want to run then runs the specific function for it and returns the steps taken from start node to destination
'''
def main():
    grids      = [genRandGrid(5,5),genRandGrid(7,7)] 
    obstacles  = ['foo','boo']     # FIXME [for now the grid is generated with random obstacles]
    starts     = [(0,0),(1,2)]     
    targets    = [(3,4),(5,7)]     
    numRuns    = 10
    navAlgs     = [2,2]             


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
    
