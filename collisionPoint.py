import math

def collisionPoint(rx,ry,angle,ax,ay,bx,by):
    '''
    a function that takes in top left corner of obstacle (xmin,ymax) and bottom right corner of obstacle (xmax,ymin) as well as two points (coordinates) on a trajectory (straight line)
    and returns the point at which the line will intersect with the obstacle
    '''

    angleRadian      = math.radians(angle)
    sinAngle         = round(math.sin(angleRadian),2)
    cosAngle         = round(math.cos(angleRadian),2)
    
    x2               = rx + sinAngle

    y2               = ry - cosAngle
    
   
    vx               = x2-rx
    vy               = y2-ry
    p                = [-vx, vx, -vy, vy]
    q                = [rx-ax, bx-rx, ry-ay, by-ry]
    
    u1               = 0
    u2               = 1   
    
    
    
    for i in range(4):
        if p[i] == 0:
            if q[i] < 0:
                return (None,None)
        else:
            t = q[i]/p[i]
            if p[i] < 0 and u1 < t:
                u1 = t
            elif p[i] > 0 and u2 > t:
                u2 = t 
    
    xcollide = rx + u1*vx
    ycollide = ry + u1*vy
    
    if xcollide < ax or xcollide > bx or ycollide < ay or ycollide > by:
        return(None, None)
        
    if xcollide != rx and ycollide != ry and xcollide != x2 and ycollide != y2:
        a = (xcollide - rx  , ycollide - ry)
        b = (xcollide - x2  , ycollide - y2)
        
        
        angleAC = math.degrees(math.acos(  ((a[0]*b[0])+(a[1]*b[1]))/( (math.sqrt( a[0]**2 + a[1]**2 ) * (math.sqrt( b[0]**2 + b[1]**2 )))) ) )
        
        if angleAC != 180   :
            
            if (abs(xcollide - rx)< abs(xcollide-x2))or (abs(ycollide - ry)< abs(ycollide-y2)): 
                return (None, None)
        
 
    return (round(xcollide,3),round(ycollide,3))
    
#============================ main ============================================

TESTCASES = [
    #  rx    ry    angle   ax  ay    bx   by -> cx  cy
    (  9.9 , 5    , 90  ,  10 , 0  , 15 , 10 , 10  , 5   ),
    (  5   , 5    , 90  ,  10 , 0  , 15 , 10 , 10  , 5   ),
    (  5   , 5    , 135 ,  10 , 0  , 15 , 10 , 10  , 10  ),
    (  5   , 5    , -90 ,  10 , 0  , 15 , 10 , None, None),
    (  5   , 5    ,  0  ,  10 , 0  , 15 , 10 , None, None),
    (  5   , 5    , 45  ,  10 , 0  , 15 , 10 , 10  , 0   ),
    (  5   , 5    , 280 ,  10 , 0  , 15 , 10 , None, None),
    (  20  , 13   , -45 ,  5  , 5  , 15 , 10 , 15  , 8   ),
    (  20  , 13   , 90  ,  5  , 5  , 15 , 10 , None, None),
    (  20  , 13   , 270 ,  5  , 5  , 15 , 10 , None, None),
    (  10  , 2    , 180 ,  5  , 5  , 15 , 10 , 10  , 5   ),
    (  10  , 2    , 90  , 5   , 5  , 15 , 10 , None, None),
    (  9   , 1    , 225 , 4   , 2  , 8  , 4  , 8   , 2   ),
    (  7   , 4    , 0   , 4   , 2  , 8  , 4  , 7   , 4   ),
    (  6   , 4.01 , 0   , 4   , 2  , 8  , 4  , 6   , 4   ),
    (  11  , 5    , 225 , 4   , 2  , 8  , 4  , None, None),
    
    
    
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
