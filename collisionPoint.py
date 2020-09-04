import math

'''
a function that takes in top left corner of obstacle (xmin,ymax) and bottom right corner of obstacle (xmax,ymin) as well as two points (coordinates) on a trajectory (straight line)
and returns the point at which the line will intersect with the obstacle
'''
def collisionPoint(x1,y1,angle,xmin,ymin,xmax,ymax):
    
    angleRadian = math.radians(angle)
    print(angleRadian)
    x2 = x1 + round(math.sin(angleRadian),2)
    y2 = y1 + round(math.cos(angleRadian),2)
    print(x2,y2)
    
    
    vx = x2-x1
    vy = y2-y1
    p  = [-vx, vx, -vy, vy]
    q  = [x1-xmin, xmax-x1, y1-ymin, ymax-y1]
    
    u1 = 0
    u2 = 1   
    
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
    print('collosion at :', (xcollide,ycollide))
    return (xcollide,ycollide)     
    
#============================ main ============================================

TESTCASES = [
    #  rx ry angle  ax ay bx by   -> cx  cy
    (  5, 5, 90,    10, 0,15, 10,    10, 5 )
    ]

def main():
    for ( (rx,ry,angle,ax,ay,bx,by,cx,cy) in TESTCASES ):
        assert collisionPoint(rx,ry,angle,ax,ay,bx,by)==(cx,cy)
    collisionPoint( 5, 5, 90,    10, 0,15, 10)
    print('Done.')

if __name__=='__main__':
    main()
