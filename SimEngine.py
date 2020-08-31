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
    
    #=== commands from the GUI
    
    def play(self):
        '''
        (re)start the execution of the simulation
        '''
        
        raise NotImplementedError()
        
    def pause(self):
        '''
        pause the execution of the simulation
        '''
        
        raise NotImplementedError()
    
    #======================== private =========================================