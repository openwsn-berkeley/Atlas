
class SimEngine(object):
    '''
    Discrete-event simulation engine for a swarm of DotBots.
    '''
    def __init__(self):
        
        # store params
        
        # local variables
        self.currentTime  = 0
        self.events       = []
    
    #======================== public ==========================================
    
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