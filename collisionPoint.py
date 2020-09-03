import math

'''
a function that takes in top left corner of obstacle (xmin,ymax) and bottom right corner of obstacle (xmax,ymin) as well as two points (coordinates) on a trajectory (straight line)
and returns the point at which the line will intersect with the obstacle
'''
def collisionPoint(xmax,xmin,ymax,ymin,x1,y1,heading):
    
    x2 = math.cos(heading)
    y2 = math.sin(heading)
    
    
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
    return         
    
    
def main():
    #xmax, xmin, ymax, ymin, x1 , y1, heading 
    collisionPoint(30,-30,20,-20,50,-10,45)
    print('Done.')

if __name__=='__main__':
    main() 