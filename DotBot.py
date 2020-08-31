# built-in
import random
# third-party
# local
import SimEngine
import Wireless

class DotBot(object):
    '''
    A single DotBot.
    '''
    
    def __init__(self,dotBotId):
        
        # store params
        self.dotBotId             = dotBotId
        
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
        (x,y,ts) = self._computeNextBump()
        
        # remember
        self.nextBumpx  = x
        self.nextBumpy  = y
        self.nextBumpTs = ts
        
        # schedule
        self.simEngine.schedule(self.nextBumpTs,self._bump)
    
    def getPosition(self):
        '''
        "Backdoor" functions used by the simulation engine to compute where the DotBot is now.
        
        \post updates attributes position and posTs
        '''
        return (
            29*random.random(),
             7*random.random(),
        )
    
    #======================== private =========================================
    
    def _bump(self):
        '''
        Bump sensor triggered
        '''
        
        assert self.simEngine.currentTime()==self.nextBumpTs
        
        # update my position
        self.x                    = self.nextBumpx
        self.y                    = self.nextBumpy
        self.posTs                = self.simEngine.currentTime()
        
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
        raise NotImplementedError()
    