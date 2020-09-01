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
    
    MODE_PAUSE          = 'pause'
    MODE_FRAMEFORWARD   = 'frameforward'
    MODE_PLAY           = 'play'
    MODE_FASTFORWARD    = 'fastforward'
    
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
        self._mode                = self.MODE_PAUSE
        self._startTsSim          = None
        self._startTsReal         = None
        self._playSpeed           = 1.00
        self.events               = []
        self.semNumEvents         = threading.Semaphore(0)
        self.dataLock             = threading.Lock()
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
            
            # switch to MODE_PAUSE if in MODE_FRAMEFORWARD
            if self._mode==self.MODE_FRAMEFORWARD:
                self._mode=self.MODE_PAUSE
                self.semIsRunning.acquire()
            
            # wait if in MODE_PLAY
            if self._mode==self.MODE_PLAY:
                durSim  = self._currentTime-self._startTsSim
                durReal = time.time()-self._startTsReal
                if durReal*self._playSpeed<durSim:
                    time.sleep( durSim - (durReal*self._playSpeed) )
    
    #======================== public ==========================================
    
    #=== from other elements in simulator
    
    def currentTime(self):
        return self._currentTime
    
    def mode(self):
        return self._mode
    
    def formatSimulatedTime(self):
        returnVal            = []
        returnVal           += ['[']
        returnVal           += [' {0} simulated'.format(str(datetime.timedelta(seconds=self._currentTime)).split('.')[0])]
        if self._startTsSim!=None :
            durSim           = self._currentTime-self._startTsSim
            durReal          = time.time()-self._startTsReal
            if durReal>1:
                speed        = int(durSim / durReal)
            else:
                speed        = '?'
            returnVal       += ['( {0:>4} &times; )'.format(speed)]
        returnVal           += [']']
        returnVal            = ' '.join(returnVal)
        return returnVal
    
    def schedule(self,ts,cb):
        # add new event
        self.events += [(ts,cb)]
        
        # reorder list
        self.events  = sorted(self.events, key = lambda e: e[0])
        
        # release semaphore
        self.semNumEvents.release()
    
    #=== commands from the GUI
    
    def commandPause(self):
        '''
        pause the execution of the simulation
        '''
        
        with self.dataLock:
            if self._mode != self.MODE_PAUSE:
                self.semIsRunning.acquire()
            self._startTsSim  = None
            self._startTsReal = None
            self._mode        = self.MODE_PAUSE
    
    def commandFrameforward(self):
        '''
        execute next event in list of events
        '''
        
        with self.dataLock:
            if self._mode == self.MODE_PAUSE:
                self.semIsRunning.release()
            self._startTsSim  = None
            self._startTsReal = None
            self._mode        = self.MODE_FRAMEFORWARD
    
    def commandPlay(self,playSpeed):
        '''
        (re)start the execution of the simulation at moderate speed
        '''
        
        with self.dataLock:
            if self._mode == self.MODE_PAUSE:
                self.semIsRunning.release()
            self._startTsSim  = self._currentTime
            self._startTsReal = time.time()
            self._playSpeed   = playSpeed
            self._mode        = self.MODE_PLAY
    
    def commandFastforward(self):
        '''
        (re)start the execution of the simulation at full speed
        '''
        
        with self.dataLock:
            if self._mode == self.MODE_PAUSE:
                self.semIsRunning.release()
            self._startTsSim  = self._currentTime
            self._startTsReal = time.time()
            self._mode        = self.MODE_FASTFORWARD
    
    #======================== private =========================================
    
    def _handleNextEvent(self):
        assert self.events
        
        (ts,cb) = self.events.pop(0)
        
        self._currentTime = ts
        cb()
