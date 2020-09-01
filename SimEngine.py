# built-in
import threading
import time
import datetime
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
        self._currentTime         = 0    # what time is it for the DotBots
        self._runTime             = 0    # how many seconds has the computer been actively simulating?
        self._runTimePlayTs       = None # timestamp of when the play button was pressed
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
            
            # is next was clicked, acquire
            with self.dataLock:
                if self.nextClicked==True:
                    self.nextClicked = False
                    self.semIsRunning.acquire()
    
    #======================== public ==========================================
    
    #=== from other elements in simulator
    
    def currentTime(self):
        return self._currentTime
    
    def formatSimulatedTime(self):
        returnVal  = []
        returnVal += ['{0}'.format(str(datetime.timedelta(seconds=self._currentTime)).split('.')[0])]
        if self._runTime>0 or self._runTimePlayTs!=None:
            totalRuntime = self._runTime
            if self._runTimePlayTs!=None:
                totalRuntime+=time.time()-self._runTimePlayTs
            returnVal += ['({0} x)'.format(int(self._currentTime / totalRuntime))]
        returnVal = ' '.join(returnVal)
        return returnVal
    
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
            if self._runTimePlayTs == None:
                self._runTimePlayTs = time.time()
            self.isPaused = False
        
        self.semIsRunning.release()
        
    def commandPause(self):
        '''
        pause the execution of the simulation
        '''
        
        with self.dataLock:
            if self._runTimePlayTs != None:
                self._runTime      += time.time()-self._runTimePlayTs
                self._runTimePlayTs = None
            self.isPaused = True
        
        self.semIsRunning.acquire()
    
    #======================== private =========================================
    
    def _handleNextEvent(self):
        assert self.events
        
        (ts,cb) = self.events.pop(0)
        
        self._currentTime = ts
        cb()
