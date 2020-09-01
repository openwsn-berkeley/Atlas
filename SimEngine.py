# built-in
import threading
import time
# third-party
# local

class SimEngine(threading.Thread):
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
        self._currentTime         = 0
        self.events               = []
        self.semNumEvents         = threading.Semaphore(0)
        self.dataLock             = threading.Lock()
        self.nextClicked          = False
        self.isPaused             = True
        self.semIsRunning         = threading.Lock()
        self.semIsRunning.acquire()
        
        # start thread
        threading.Thread.__init__(self)
        self.name                 = 'SimEngine'
        self.daemon               = True
        self.start()
    
    #======================== thread ==========================================
    
    def run(self):
        while True:
            
            # wait for simulator to be running
            self.semIsRunning.acquire()
            self.semIsRunning.release()
            
            # wait for at least one event
            self.semNumEvents.acquire()
            
            # handle
            self._handleNextEvent()
            time.sleep(0.050) # FIXME
            
            # is next was clicked, acquire
            with self.dataLock:
                if self.nextClicked==True:
                    self.nextClicked = False
                    self.semIsRunning.acquire()
    
    #======================== public ==========================================
    
    #=== from other elements in simulator
    
    def currentTime(self):
        return self._currentTime
    
    def schedule(self,ts,cb):
        # add new event
        self.events += [(ts,cb)]
        
        # reorder list
        self.events  = sorted(self.events, key = lambda e: e[0])
        
        # release semaphore
        self.semNumEvents.release()
    
    #=== commands from the GUI
    
    def commandNext(self):
        '''
        execute next event in list of events
        '''
        
        # abort if not paused
        with self.dataLock:
            if not self.isPaused:
                return
        
        with self.dataLock:
            self.nextClicked = True
        
        self.semIsRunning.release()
    
    def commandPlay(self):
        '''
        (re)start the execution of the simulation
        '''
        
        with self.dataLock:
            self.isPaused = False
        
        self.semIsRunning.release()
        
    def commandPause(self):
        '''
        pause the execution of the simulation
        '''
        
        with self.dataLock:
            self.isPaused = True
        
        self.semIsRunning.acquire()
    
    #======================== private =========================================
    
    def _handleNextEvent(self):
        assert self.events
        
        (ts,cb) = self.events.pop(0)
        
        self._currentTime = ts
        cb()
