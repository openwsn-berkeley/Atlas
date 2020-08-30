class DotBot(object):
    '''
    A single DotBot.
    '''
    
    def __init__(self,dotBotId):
        # store params
        self.dotBotId             = dotBotId
        
        # local variables
        self.position             = None  # the "real" position, sometimes in the past a (x,y) tuple. Set to None to ensure single initialization
        self.positionTimestamp    = 0     # timestamp, in s, of when was at position
        self.heading              = 0     # the heading, a float between 0 and 360 degrees (0 indicates North)
        self.headingInaccuracy    = 0     # innaccuracy, in degrees of the heading. Actual error computed as uniform(-,+)
        self.speed                = 0     # speed, in m/s, the DotBot is going at
        self.speedInaccuracy      = 0     # innaccuracy, in m/s of the speed. Actual error computed as uniform(-,+)
    
    #======================== public ==========================================
    
    #=== public "remote control" interface of the DotBot
    
    def setInitialPosition(self,x,y)
        '''
        Call exactly once at start of simulation to exactly place the DotBot at its initial position.
        '''
        assert self.position==None
        self.position = (x,y)
    
    def setHeading(self,heading)
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
    
    def setSpeed(self,speed):
        '''
        Change the speed of the DotBot.
        Actual speed affected by self.speedInaccuracy
        Assumes applying new speed is infinitely fast.
        '''
        if self.speedInaccuracy: # cut computation in two cases for efficiency
            self.speed = speed + (-1+(2*random.random()))*self.speedInaccuracy
        else:
            self.speed = speed
    
    #=== "backdoor" functions used by the simulation engine
    
    def getPosition(self):
        '''
        Compute where the DotBot is now.
        
        \post updates attributes position and positionTimestamp
        '''
        raise NotImplementedError
    
    #======================== private =========================================
    
    