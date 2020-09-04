import math

def collisionPoint(x1,y1,angle,xmin,ymin,xmax,ymax):
    '''
    a function that takes in top left corner of obstacle (xmin,ymax) and bottom right corner of obstacle (xmax,ymin) as well as two points (coordinates) on a trajectory (straight line)
    and returns the point at which the line will intersect with the obstacle
    '''
    
    angleRadian      = math.radians(angle)
    
    x2               = x1 + round(math.sin(angleRadian),2)
    y2               = y1 + round(math.cos(angleRadian),2)
    
    vx               = x2-x1
    vy               = y2-y1
    p                = [-vx, vx, -vy, vy]
    q                = [x1-xmin, xmax-x1, y1-ymin, ymax-y1]
    
    u1               = 0
    u2               = 1   
    
    for i in range(4):
        if p[i] == 0:
            if q[i] < 0:
                continue
        else:
            t = q[i]/p[i]
            if p[i] < 0 and u1 < t:
                u1 = t
            elif p[i] > 0 and u2 > t:
                u2 = t 
    
    xcollide = x1 + u1*vx
    ycollide = y1 + u1*vy
    
    return (xcollide,ycollide)
    
#============================ main ============================================

TESTCASES = [
    #  rx ry angle  ax ay bx by   -> cx  cy
    (  5, 5, 90,    10, 0,15, 10,    10,    5 ),
    (  5, 5,135,    10, 0,15, 10,    10,   10 ),
    (  5, 5,-90,    10, 0,15, 10,  None, None ),
    (  5, 5,  0,    10, 0,15, 10,  None, None ),
    (  5, 5, 45,    10, 0,15, 10,    10,    0 ),
]

def main():
    for (rx,ry,angle,ax,ay,bx,by,cx,cy) in TESTCASES:
        output  = []
        returnVal = collisionPoint(rx,ry,angle,ax,ay,bx,by)
        output += ['rx={0:>3} ry={1:>3} angle={2:>3} ax={3:>3} ay={4:>3} bx={5:>3} by={6:>2} --> {7:>20}  '.format(rx,ry,angle,ax,ay,bx,by,str(returnVal))]
        if returnVal==(cx,cy):
            output += ['PASS']
        else:
            output += ['FAIL expected {0}'.format((cx,cy))]
        output = ''.join(output)
        print(output)
    print('Done.')

if __name__=='__main__':
    main()
