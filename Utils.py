import math

def distance(pos1,pos2):
    (x1,y1) = pos1
    (x2,y2) = pos2
    return math.sqrt( (x1-x2)**2 + (y1-y2)**2 )

def computeCurrentPosition(currentX,currentY,heading,speed,duration):
    newX = currentX + duration * math.cos(math.radians(heading - 90)) * speed
    newY = currentY + duration * math.sin(math.radians(heading - 90)) * speed
    newX = round(newX, 3)
    newY = round(newY, 3)
    return (newX,newY)