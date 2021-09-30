# built-in
# third-party
# local

class Wireless(object):
    '''
    The wireless medium through which DotBot and orchestrator communicate.
    '''
    
    PDR = 1
    
    # singleton pattern
    _instance   = None
    _init       = False
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Wireless, cls).__new__(cls, *args, **kwargs)
        return cls._instance
    
    def __init__(self):
        
        # singleton patterm
        if self._init:
            return
        self._init = True
        
        # local variables
        self.dotbots      = None
        self.orchestrator = None
    
    #======================== public ==========================================
    
    def indicateElements(self,dotbots,orchestrator):
        assert self.dotbots==None
        assert self.orchestrator==None
        
        self.dotbots      = dotbots
        self.orchestrator = orchestrator
    
    def toDotBots(self,msg):
        for dotbot in self.dotbots:
            if self.PDR==1:
                dotbot.fromOrchestrator(msg)
            else:
                raise NotImplementedError()
    
    def toOrchestrator(self,msg):
        if self.PDR==1:
            self.orchestrator.fromDotBot(msg)
        else:
            raise NotImplementedError()
    
    #======================== private =========================================
