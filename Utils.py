import math

def distance(pos1,pos2):
    (x1,y1) = pos1
    (x2,y2) = pos2
    return math.sqrt( (x1-x2)**2 + (y1-y2)**2 )