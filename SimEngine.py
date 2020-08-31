# built-in
# third-party
# local

class SimEngine(object):
    '''
    Discrete-event simulation engine for a swarm of DotBots.
    '''
    
    # singleton pattern
    _instance   = None
    _init       = False
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SimEngine, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        
        # singleton patterm
        if self._init:
            return
        self._init = True
        
        # local variables
        self._currentTime  = 0
        self.events       = []
    
    #======================== public ==========================================
    
    #=== from other elements in simulator
    
    def currentTime(self):
        return self._currentTime
    
    def schedule(self,ts,cb):
        # add new event
        self.events += [(ts,cb)]
        
        # reorder list
        self.events  = sorted(self.events, key = lambda e: e[0])
    
    #=== commands from the GUI
    
    def commandNext(self):
        '''
        execute next event in list of events
        '''
        
        self._handleNextEvent()
    
    def commandPlay(self):
        '''
        (re)start the execution of the simulation
        '''
        
        raise NotImplementedError()
        
    def commandPause(self):
        '''
        pause the execution of the simulation
        '''
        
        raise NotImplementedError()
    
    #======================== private =========================================
    
    def _handleNextEvent(self):
        assert self.events
        
        (ts,cb) = self.events.pop(0)
        
        self._currentTime = ts
        cb()