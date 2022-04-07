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
        self.last_ts              = 0
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

            # handle next event
            (ts,cb,tag) = self.events.pop(0)

            if ts != self._currentTime:
                self.last_ts = time.time()
            if self.last_ts - time.time() > 300:
                print(self.last_ts, time.time())
                assert  ts != self._currentTime
            self._currentTime = ts

            if tag == 'selfDestruct':
                break

            cb()

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
    
    #=== admin
    
    def destroy(self): 
        self._instance   = None
        self._init       = False
    
    def runToCompletion(self,startFunc):
        assert self._currentTime==0
        self.schedule(0,startFunc) # schedule the first event
        self.join()                # block until simEngine thread ends
        
        return self._currentTime
    
    def schedule(self,ts,cb,tag=None):
        # add new event
        self.events += [(ts,cb,tag)]
        # reorder list
        self.events  = sorted(self.events, key = lambda e: e[0])
        # release semaphore (increments its internal counter)
        self.semNumEvents.release()

    def cancelEvent(self, tag):
        idx = 0
        while idx<len(self.events):
            if self.events[idx][2]==tag:
                self.events.pop(idx)
            else:
                idx += 1


    def completeRun(self):
        self.schedule(self._currentTime,None,tag='selfDestruct')
    
    #=== helper functions

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
                simSpeed     = int(durSim / durReal)
            else:
                simSpeed     = '?'
            returnVal       += ['( {0:>4} &times; )'.format(simSpeed)]
        returnVal           += [']']
        returnVal            = ' '.join(returnVal)
        return returnVal
    
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
        (re)start the execution of the simulation at moderate simSpeed
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
        (re)start the execution of the simulation at full simSpeed
        '''
        
        with self.dataLock:
            if self._mode == self.MODE_PAUSE:
                self.semIsRunning.release()
            self._startTsSim  = self._currentTime
            self._startTsReal = time.time()
            self._mode        = self.MODE_FASTFORWARD
    
    #======================== private =========================================
