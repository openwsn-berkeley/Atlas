'''
simulation of online and offline navigation algorithms

user has option to either give a specific grid through a config file, or to have the simulator generate a random grid :
'''

import json
import random
import matplotlib.pyplot as plt
import numpy as np

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
performs online obstacle avoidance and returns the path found 
'''  
def ObstacleAvoidAlg(start, target,grid):
    
    currentNode = start
    onlinePath = [start]
    
    while (currentNode != target):
        x=currentNode[0]
        y=currentNode[1]
        neighbourNodes = [(x+1,y),(x+1,y+1),(x,y+1),(x-1,y+1),(x-1,y),(x-1,y-1),(x,y-1),(x+1,y-1)]
        avaliableNext=[]
        print(neighbourNodes)
        for node in neighbourNodes:
            print("node = ", node)
            NN=node
            #print(NN[0],NN[1])
            #print(grid[NN[0]][NN[1]])
            if (NN[0])>=0 and (NN[1])>=0 and (grid[NN[0]][NN[1]])==1:
                if(node != (0,0)) and (node in onlinePath) == False:
                    idx=neighbourNodes.index(node)
                    print("index =" , idx)
                    avaliableNext.append(node)        
        print(avaliableNext)
        if avaliableNext==[]:
            return print("no path avaliable")
        else:
            moveTo = avaliableNext[random.randint(0,len(avaliableNext)-1)]
            print(moveTo)
            onlinePath.append(moveTo)
            print("online path so far is ", onlinePath)
            currentNode=moveTo
    
    print(onlinePath)
    return onlinePath

'''
calculates steps taken from source to destination
'''
def singleRun(grid,obstacle,start,target,navAlg,runRun):
    steps = random.randint(10,100)
    return steps

#============================ main ============================================

'''
asks user for the navigation algorithm they want to run then runs the specific function for it and returns the steps taken from start node to destination
'''
def main():
    grids      = [(20,20),(50,50)] # FIXME
    obstacles  = ['foo','bar']     # FIXME
    starts     = [(1,2),(3,4)]     # FIXME
    targets    = [(5,6),(7,8)]     # FIXME
    numRuns    = 100
    navAlg     = None              # FIXME
    rows = random.randint(5,21)
    cols = random.randint(5,21)
    grid = genRandGrid(rows,cols)
    start=(0,0)
    target=(5,5)
    ObstacleAvoidAlg(start,target,grid)
    # run all simulations
    with open('HNOO.log','w') as f:
        for grid in grids:
            for obstacle in obstacles:
                for start in starts:
                    for target in targets:
                        for runRun in range(numRuns):
                        
                            # run  single run
                            steps = singleRun(grid,obstacle,start,target,navAlg,runRun)
                            
                            # log the results
                            f.write(json.dumps(
                                {
                                    'grid':     grid,
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
   # plt.show()
   # plt.savefig('HNOO.png')
    
    
    print('Done.')
    
if __name__=='__main__':
    main()
    
