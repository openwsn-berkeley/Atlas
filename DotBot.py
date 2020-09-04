# built-in
import random
import math
import itertools
import threading
# third-party
# local
import SimEngine
import Wireless
import Utils as u

class DotBot(object):
    '''
    A single DotBot.
    '''
    
    def __init__(self,dotBotId,floorplan):
        
        # store params
        self.dotBotId                  = dotBotId
        self.floorplan                 = floorplan
        
        # local variables
        self.simEngine                 = SimEngine.SimEngine()
        self.wireless                  = Wireless.Wireless()
        self.x                         = None  # the "real" position, sometimes in the past. Set to None to ensure single initialization
        self.y                         = None
        self.posTs                     = 0     # timestamp, in s, of when was at position
        self.lastCommandIdReceived     = None  # set to None as not a valid command Id
        self.headingRequested          = 0     # the heading, a float between 0 and 360 degrees (0 indicates North) as requested by the orchestrator
        self.headingInaccuracy         = 0     # innaccuracy, in degrees of the heading. Actual error computed as uniform(-,+)
        self.headingActual             = 0     # actual heading, taking into account inaccuracy
        self.speedRequested            = 0     # speed, in m/s, as requested by the orchestrator
        self.speedInaccuracy           = 0     # innaccuracy, in m/s of the speed. Actual error computed as uniform(-,+)
        self.speedActual               = 0     # actual speed, taking into account inaccuracy
        self.next_bump_x               = None  # coordinate the DotBot will bump into next
        self.next_bump_y               = None
        self.next_bump_ts              = None  # time at which DotBot will bump
    
    #======================== public ==========================================
        
    def setInitialPosition(self,x,y):
        '''
        Call exactly once at start of simulation to exactly place the DotBot at its initial position.
        '''
        assert self.x==None
        assert self.y==None
        self.x      = x
        self.y      = y
        self.posTs  = self.simEngine.currentTime()
    
    def fromOrchestrator(self,packet):
        '''
        Received a packet from the orchestrator
        '''
        
        # extract portion of orchestrator message which is for me (shorthand)
        myMsg = packet[self.dotBotId]
        
        # disregard duplicate command
        if myMsg['commandId']==self.lastCommandIdReceived:
            return
        
        # remember what I was asked
        self.lastCommandIdReceived     = myMsg['commandId']
        self.headingRequested          = myMsg['heading']
        self.speedRequested            = myMsg['speed']
        
        # apply heading and speed from packet
        self._setHeading(myMsg['heading'])
        self._setSpeed(  myMsg['speed'])
        
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
        
        # gather state
        now              = self.simEngine.currentTime()
        x                = self.x
        y                = self.y
        posTs            = self.posTs
        headingActual    = self.headingActual
        speedActual      = self.speedActual
        
        # update position
        newX                 = x + (now-posTs)*math.cos(math.radians(headingActual-90))*speedActual
        newY                 = y + (now-posTs)*math.sin(math.radians(headingActual-90))*speedActual
        
        # do NOT write back any results to the DotBot's state as race condition possible
        return {
            'x':           newX,
            'y':           newY,
            'heading':     self.headingActual,
            'speed':       self.speedActual,
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
        self.x               = self.next_bump_x
        self.y               = self.next_bump_y
        self.posTs           = self.next_bump_ts
        
        # stop moving
        self.speedActual     = 0
        
        # report bump to orchestrator
        self.wireless.toOrchestrator({
            'dotBotId':      self.dotBotId,
            'bumpTs':        self.simEngine.currentTime(),
        })
    
    def _setHeading(self,heading):
        '''
        Change the heading of the DotBot.
        Actual heading affected by self.headingInaccuracy
        Assumes applying new heading is infinitely fast.
        '''
        assert heading>=0
        assert heading<360
        if self.headingInaccuracy: # cut computation in two cases for efficiency
            self.headingActual = heading + (-1+(2*random.random()))*self.headingInaccuracy
        else:
            self.headingActual = heading
    
    def _setSpeed(self,speed):
        '''
        Change the speed of the DotBot.
        Actual speed affected by self.speedInaccuracy
        Assumes applying new speed is infinitely fast.
        '''
        if self.speedInaccuracy: # cut computation in two cases for efficiency
            self.speedActual = speed + (-1+(2*random.random()))*self.speedInaccuracy
        else:
            self.speedActual = speed
    
    def _computeNextBump(self):
        
        if   self.headingActual in [ 90,270]:
            # horizontal edge case
            
            north_x      = None # doesn't cross
            south_x      = None # doesn't cross
            west_y       = self.y
            east_y       = self.y
            
        elif self.headingActual in [  0,180]:
            # vertical edge case
            
            north_x     = self.x
            south_x     = self.x
            west_y      = None # doesn't cross
            east_y      = None # doesn't cross
        
        else:
            # general case
             
            # find equation of trajectory as y = a*x + b
            a           = math.tan(math.radians(self.headingActual-90))
            b           = self.y - (a*self.x)
            
            # compute intersection points with 4 walls
            north_x     = (0                    -b)/a # intersection with North wall (y=0)
            south_x     = (self.floorplan.height-b)/a # intersection with South wall (y=self.floorplan.height)
            west_y      = 0*a+b                       # intersection with West wall (x=0)
            east_y      = self.floorplan.width*a+b    # intersection with West wall (x=self.floorplan.width)
        
        # pick the two intersection points on the floorplan perimeter
        valid_intersections = []
        if (north_x!=None and 0<=north_x and north_x<=self.floorplan.width):
            valid_intersections += [(             north_x,                    0)]
        if (south_x!=None and 0<=south_x and south_x<=self.floorplan.width):
            valid_intersections += [(             south_x,self.floorplan.height)]
        if (west_y!=None  and 0<=west_y  and west_y<=self.floorplan.height):
            valid_intersections += [(                   0,               west_y)]
        if (east_y!=None  and 0<=east_y  and east_y<=self.floorplan.height):
            valid_intersections += [(self.floorplan.width,               east_y)]
        
        # if mote than 2 valid points, pick the pair that is furthest appart
        if len(valid_intersections)>2:
            distances = [(u.distance(a,b),a,b) for (a,b) in itertools.product(valid_intersections,valid_intersections)]
            distances = sorted(distances,key = lambda e: e[0])
            valid_intersections = [distances[-1][1],distances[-1][2]]
        assert len(valid_intersections)==2
        
        # pick the correct intersection point given the heading of the robot
        (x_int0,y_int0) = valid_intersections[0]
        (x_int1,y_int1) = valid_intersections[1]
        if    self.headingActual==0:
            # going up
            
            # pick top-most intersection
            if y_int0<y_int1:
                (bump_x,bump_y) = (x_int0,y_int0)
            else:
                (bump_x,bump_y) = (x_int1,y_int1)
        elif ( 0<self.headingActual and self.headingActual<180 ):
            # going right
            
            # pick right-most intersection
            if x_int1<x_int0:
                (bump_x,bump_y) = (x_int0,y_int0)
            else:
                (bump_x,bump_y) = (x_int1,y_int1)
        elif  self.headingActual==180:
            # going down
            
            # pick bottom-most intersection
            if y_int1<y_int0:
                (bump_x,bump_y) = (x_int0,y_int0)
            else:
                (bump_x,bump_y) = (x_int1,y_int1)
        else:
            # going left
            
            # pick right-most intersection
            if x_int0<x_int1:
                (bump_x,bump_y) = (x_int0,y_int0)
            else:
                (bump_x,bump_y) = (x_int1,y_int1)
        
        # compute time to bump
        timetobump = u.distance((self.x,self.y),(bump_x,bump_y))/self.speedActual
        bump_ts    = self.posTs+timetobump
        
        # round
        bump_x     = round(bump_x,3)
        bump_y     = round(bump_y,3)
        
        return (bump_x,bump_y,bump_ts)
