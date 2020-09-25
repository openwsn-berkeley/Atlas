import math


def collisionPoint(rx, ry, angle, ax, ay, bx, by):
    '''
    a function that takes in top left corner of obstacle (xmin,ymax) and bottom right corner of obstacle (xmax,ymin) as well as two points (coordinates) on a trajectory (straight line)
    and returns the point at which the line will intersect with the obstacle
    '''


    angleRadian = math.radians(angle)
    sinAngle = math.sin(angleRadian)
    cosAngle = math.cos(angleRadian)

    x2 = rx + sinAngle

    y2 = ry - cosAngle

    vx = x2 - rx
    vy = y2 - ry
    p = [-vx, vx, -vy, vy]
    q = [rx - ax, bx - rx, ry - ay, by - ry]

    u1 = -math.inf
    u2 = math.inf

    for i in range(4):
        if p[i] != 0:

            t = q[i] / p[i]
            if p[i] < 0 and u1 < t:
                u1 = t
            elif p[i] > 0 and u2 > t:
                u2 = t


    xcollide = rx + u1 * vx
    ycollide = ry + u1 * vy

    xcollide2 = rx + u2 * vx
    ycollide2 = ry + u2 * vy


    if xcollide < ax or xcollide > bx or ycollide < ay or ycollide > by:
        return (None, None)

    if not(xcollide == rx and ycollide == ry):
        a = (rx - xcollide, ry - ycollide)
        b = (rx - x2, ry - y2)

        cosangle = ((a[0] * b[0]) + (a[1] * b[1])) / (
        (math.sqrt(a[0] ** 2 + a[1] ** 2) * (math.sqrt(b[0] ** 2 + b[1] ** 2))))
        angleAC = math.degrees((math.acos(round(cosangle, 3))))

        if angleAC == 0:
            return (round(xcollide, 3), round(ycollide, 3))
        else:
            return (None, None)
           # if (abs(xcollide - rx) < abs(xcollide - x2)) or (abs(ycollide - ry) < abs(ycollide - y2)):
           #     return (None, None)
    else:
        if (xcollide2 == ax  or xcollide2 == bx or ycollide2 == ay or ycollide2 == by):
            #(x2 > ax and x2 < bx and y2 > ay and y2 < by)):
            if not (xcollide == xcollide2 and ycollide == ycollide2):
                return (round(xcollide, 3), round(ycollide, 3))
        else:
            return(None, None)
    return (None, None)
    
#============================ main ============================================

TESTCASES = [
    #  rx    ry    angle   ax  ay    bx   by -> cx  cy
    (  10 , 5    , 90 ,  10 , 0  , 15 , 10 , 10  , 5   ),
    (  5   , 5    , 90  ,  10 , 0  , 15 , 10 , 10  , 5   ),
    (  5   , 5    , 135 ,  10 , 0  , 15 , 10 , 10  , 10  ),
    (  5   , 5    , -90 ,  10 , 0  , 15 , 10 , None, None),
    (  5   , 5    ,  0  ,  10 , 0  , 15 , 10 , None, None),
    (  5   , 5    , 45  ,  10 , 0  , 15 , 10 , 10  , 0   ),
    (  5   , 5    , 280 ,  10 , 0  , 15 , 10 , None, None),
    (  20  , 13   , -45 ,  5  , 5  , 15 , 10 , 15  , 8   ),
    (  20  , 13   , 90  ,  5  , 5  , 15 , 10 , None, None),
    (  20  , 13   , 270 ,  5  , 5  , 15 , 10 , None, None),
    (  10  , 2    , 90  , 5   , 5  , 15 , 10 , None, None),
    (  9   , 1    , 225 , 4   , 2  , 8  , 4  , 8   , 2   ),
    (  7   , 4    , 0   , 4   , 2  , 8  , 4  , 7   , 4   ),
    (  6   , 4.01 , 0   , 4   , 2  , 8  , 4  , 6   , 4   ),
    (  11  , 5    , 225 , 4   , 2  , 8  , 4  , None, None),
    (2,10,90,5,8,10,13,5,10),
    (2,10,-90,5,8,10,13,None, None),
    (5,10,90,5,8,10,13,5,10),
    (5,10,-90,5,8,10,13,None,None),
    (2,14,90,5,8,10,13,None,None),
    (4,13,90,5,8,10,13,5,13),
    (4,14,45,5,8,10,13,5,13),
    (5,13,135,5,8,10,13,None,None),
    (13.1,9.9,70,5,8,10,13,None,None),
    (6,15,45,5,8,10,13,8,13),
    (7,14,225,5,8,10,13,None,None),
    (4.5,10,30,5,8,10,13,5,9.134),
    (14.791,4.0,145,15,4,16,5,None,None),
     (4.813,4.0,31,4,3,5,4,4.813,4.0),
     (4.913,2,202,4,2,5,3,4.913,2),
     (4.193,2.0,138,4,2,5,3,4.193,2.0),
    (2,3,-45,1,2,2,3,2,3),

    
    
    
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
