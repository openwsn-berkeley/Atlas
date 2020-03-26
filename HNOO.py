#simulation of online and offline navigation algorithms

#user has option to either give a specific grid through a config file, or to have the simulator generate a random grid :

#get gid matrix from config file
def getGrid():
    grid = []
    return grid

#generate random grid
def genRandGrid():
    RandGrid= []
    return RandGrid
 
#ask user for start node 
def getStartNode():
    return startNode

#ask user for target node    
def getTargetNode():
    return targetNode

#performs A star search and returns the path found   
def AstarAlg():
    astarPath = []
    return astarPath
    
#performs online obstacle avoidance and returns the path found   
def ObstacleAvoidAlg():
    onlinePath = []
    return onlinePath

#calculates steps taken from source to destination
def totalSteps():
    return steps
    

#asks user for the navigation algorithm they want to run then runs the specific function for it and returns the steps taken from start node to destination   
def main():
    return totalSteps