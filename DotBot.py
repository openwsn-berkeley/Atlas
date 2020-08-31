# built-in
import random
import math
# third-party
# local
import SimEngine
import Wireless

class DotBot(object):
    '''
    A single DotBot.
    '''
    
    def __init__(self,dotBotId,floorplan):
        
        # store params
        self.dotBotId             = dotBotId
        self.floorplan            = floorplan
        
        # local variables
        self.simEngine            = SimEngine.SimEngine()
        self.wireless             = Wireless.Wireless()
        self.x                    = None  # the "real" position, sometimes in the past. Set to None to ensure single initialization
        self.y                    = None
        self.posTs                = 0     # timestamp, in s, of when was at position
        self.heading              = 0     # the heading, a float between 0 and 360 degrees (0 indicates North)
        self.headingInaccuracy    = 0     # innaccuracy, in degrees of the heading. Actual error computed as uniform(-,+)
        self.speed                = 0     # speed, in m/s, the DotBot is going at
        self.speedInaccuracy      = 0     # innaccuracy, in m/s of the speed. Actual error computed as uniform(-,+)
        self.next_bump_x          = None  # coordinate the DotBot will bump into next
        self.next_bump_y          = None
        self.next_bump_ts         = None  # time at which DotBot will bump
    
    #======================== public ==========================================
        
    def setInitialPosition(self,x,y):
        '''
        Call exactly once at start of simulation to exactly place the DotBot at its initial position.
        '''
        assert self.x==None
        assert self.y==None
        self.x = x
        self.y = y
        self.posTs = self.simEngine.currentTime()
    
    def fromOrchestrator(self,packet):
        '''
        Received a packet from the orchestrator
        '''
        
        # apply heading and speed from packet
        self._setHeading(packet[self.dotBotId]['heading'])
        self._setSpeed(  packet[self.dotBotId]['speed'])
        
        # compute when/where next bump will happen
        (bump_x,bump_y,bump_ts) = self._computeNextBump()
        
        # remember
        self.next_bump_x  = bump_x
        self.next_bump_y  = bump_y
        self.next_bump_ts = bump_ts
        
        # schedule
        self.simEngine.schedule(self.next_bump_ts,self._bump)
    
    def getAttitude(self):
        '''
        "Backdoor" functions used by the simulation engine to compute where the DotBot is now.
        
        \post updates attributes position and posTs
        '''
        return {
            'x':           self.x,
            'y':           self.y,
            'heading':     self.heading,
            'speed':       self.speed,
            'next_bump_x': self.next_bump_x,
            'next_bump_y': self.next_bump_y,
        }
    
    #======================== private =========================================
    
    def _bump(self):
        '''
        Bump sensor triggered
        '''
        
        assert self.simEngine.currentTime()==self.next_bump_ts
        
        # update my position
        self.x                    = self.next_bump_x
        self.y                    = self.next_bump_y
        self.posTs                = self.next_bump_ts
        
        # stop moving
        self.speed                = 0
        
        # report bump to orchestrator
        self.wireless.toOrchestrator({
            'dotBotId': self.dotBotId,
            'bumpTs':   self.simEngine.currentTime(),
        })
    
    def _setHeading(self,heading):
        '''
        Change the heading of the DotBot.
        Actual heading affected by self.headingInaccuracy
        Assumes applying new heading is infinitely fast.
        '''
        assert heading>=0
        assert heading<=360
        if self.headingInaccuracy: # cut computation in two cases for efficiency
            self.heading = heading + (-1+(2*random.random()))*self.headingInaccuracy
        else:
            self.heading = heading
    
    def _setSpeed(self,speed):
        '''
        Change the speed of the DotBot.
        Actual speed affected by self.speedInaccuracy
        Assumes applying new speed is infinitely fast.
        '''
        if self.speedInaccuracy: # cut computation in two cases for efficiency
            self.speed = speed + (-1+(2*random.random()))*self.speedInaccuracy
        else:
            self.speed = speed
    
    def _computeNextBump(self):
        
        if   self.heading in [ 90,270]:
            # horizontal edge case
            
            north_x      = None # doesn't cross
            south_x      = None # doesn't cross
            west_y       = self.y
            east_y       = self.y
            
        elif self.heading in [  0,180]:
            # vertical edge case
            
            north_x      = self.x
            south_x      = self.x
            west_y       = None # doesn't cross
            east_y       = None # doesn't cross
        
        else:
            # general case
             
            # find equation of trajectory as y = a*x + b
            a = math.tan(self.heading)
            b = self.y - (a/self.x)
            print(a,b)
            
            # compute intersection points with 4 walls
            if a:
                north_x = (0                    -b)/a # intersection with North wall (y=0)
                south_x = (self.floorplan.height-b)/a # intersection with South wall (y=self.floorplan.height)
            else:
                north_x = None
                south_x = None
            west_y      = 0*a+b                       # intersection with West wall (x=0)
            east_y      = self.floorplan.width*a+b    # intersection with West wall (x=self.floorplan.width)
        
        # pick the two intersection points on the floorplan perimeter
        valid_intersections = []
        if (north_x!=None and 0<=north_x and north_x<=self.floorplan.width):
            valid_intersections += [(north_x,0)]
        if (south_x!=None and 0<=south_x and south_x<=self.floorplan.width):
            valid_intersections += [(south_x,self.floorplan.height)]
        if (west_y!=None  and 0<=west_y  and west_y<=self.floorplan.height):
            valid_intersections += [(0,west_y)]
        if (east_y!=None  and 0<=east_y  and east_y<=self.floorplan.height):
            valid_intersections += [(self.floorplan.height,east_y)]
        assert len(valid_intersections)==2
        
        # pick the correct intersection point given the heading of the robot
        (x_int0,y_int0) = valid_intersections[0]
        (x_int1,y_int1) = valid_intersections[1]
        if   (  0<=self.heading and self.heading<90 ):
            # first quadrant
            if (self.x<=x_int0 and y_int0<=self.y):     # x higher, y lower
                (bump_x,bump_y) = (x_int0,y_int0)
            else:
                (bump_x,bump_y) = (x_int1,y_int1)
        elif ( 90<=self.heading and self.heading<180):
            # first quadrant
            if (self.x<=x_int0 and self.y<=y_int0):     # x higher, y higher
                (bump_x,bump_y) = (x_int0,y_int0)
            else:
                (bump_x,bump_y) = (x_int1,y_int1)
        elif (180<=self.heading and self.heading<270):
            # third quadrant
            if (x_int0<=self.x and self.y<=y_int0):     # x lower, y higher
                (bump_x,bump_y) = (x_int0,y_int0)
            else:
                (bump_x,bump_y) = (x_int1,y_int1)
        else:
            # forth quadrant
            if (x_int0<=self.x and y_int0<=self.y):     # x lower, y lower
                (bump_x,bump_y) = (x_int0,y_int0)
            else:
                (bump_x,bump_y) = (x_int1,y_int1)
        
        # compute time to bump
        distance   = math.sqrt( (self.x-bump_x)**2 + (self.y-bump_y)**2 )
        timetobump = distance/self.speed
        bump_ts    = self.posTs+timetobump
        
        return (bump_x,bump_y,bump_ts)
