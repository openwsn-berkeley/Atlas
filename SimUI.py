# built-in
import threading
import webbrowser
import time
# third-party
import bottle
# local
import SimEngine
import SimVersion

class SimUI(object):
    '''
    Web-based User Interface of the simulator.
    '''
    
    TCPPORT = 8080
    
    def __init__(self):
    
        # store params
        self.floorplan       = None
        self.dotbots         = []
        self.orchestrator    = None
        
        # local variables
        self.simEngine       = SimEngine.SimEngine()
        
        # start web server
        self.websrv          = bottle.Bottle()
        self.websrv.route('/',                        'GET',    self._webhandle_root_GET)
        self.websrv.route('/static/<filename>',       'GET',    self._webhandle_static_GET)
        self.websrv.route('/floorplan.json',          'GET',    self._webhandle_floorplan_GET)
        self.websrv.route('/dotbots.json',            'GET',    self._webhandle_dotbots_GET)
        self.websrv.route('/frameforward',            'POST',   self._webhandle_frameforward_POST)
        self.websrv.route('/play',                    'POST',   self._webhandle_play_POST)
        self.websrv.route('/fastforward',             'POST',   self._webhandle_fastforward_POST)
        self.websrv.route('/pause',                   'POST',   self._webhandle_pause_POST)
        webthread = threading.Thread(
            target = self._bottle_try_running_forever,
            args   = (self.websrv.run,),
            kwargs = {
                'host'          : '127.0.0.1',
                'port'          : self.TCPPORT,
                'quiet'         : True,
                'debug'         : False,
            }
        )
        webthread.name       = 'WebServer'
        webthread.daemon     = True
        webthread.start()
        
        # open browser
        webbrowser.open('http://127.0.0.1:{0}'.format(self.TCPPORT))
    
    #======================== public ==========================================
    
    def updateObjectsToQuery(self,floorplan,dotbots,orchestrator):
        self.floorplan       = floorplan
        self.dotbots         = dotbots
        self.orchestrator    = orchestrator
    
    #======================== private =========================================
    
    #=== web handles
    
    def _webhandle_root_GET(self):
        return bottle.template(
            'SimUI',
            pagetitle   = 'DotBot Simulator',
            version     = SimVersion.formatVersion(),
        )
    
    def _webhandle_static_GET(self,filename):
        return bottle.static_file(filename, root='static/')
    
    def _webhandle_floorplan_GET(self):
        try:
            returnVal = self.floorplan.getJSON()
        except AttributeError:
            print('poipoipoi _webhandle_floorplan_GET')
            returnVal = ''
        return returnVal
    
    def _webhandle_dotbots_GET(self):
        simulatedTime = self.simEngine.currentTime()
        
        try:
            orchestratorView = self.orchestrator.getView()
            returnVal = {
                'mode':                self.simEngine.mode(),
                'simulatedTime':       self.simEngine.formatSimulatedTime(),
                'dotbots':             [],
                'discomap':            orchestratorView['discomap'],
            }
            for dotbot in self.dotbots:
                returnVal['dotbots'] += [dotbot.getPositionHeadingSpeed()]
            for (dotbot,orchestratorview) in zip(returnVal['dotbots'],orchestratorView['dotbots']):
                dotbot['orchestratorview_x'] = orchestratorview['x']
                dotbot['orchestratorview_y'] = orchestratorview['y']
        except AttributeError:
            print('poipoipoi _webhandle_dotbots_GET')
            import traceback
            traceback.print_exc()
            returnVal = ''
        
        return returnVal
     
    def _webhandle_frameforward_POST(self):
        self.simEngine.commandFrameforward()
     
    def _webhandle_play_POST(self):
        rxjson = bottle.request.json
        self.simEngine.commandPlay(rxjson['speed'])
    
    def _webhandle_fastforward_POST(self):
        self.simEngine.commandFastforward()
    
    def _webhandle_pause_POST(self):
        self.simEngine.commandPause()
    
    #=== web server admin
    
    def _bottle_try_running_forever(self,*args,**kwargs):
        RETRY_PERIOD = 3
        while True:
            try:
                args[0](**kwargs) # blocking
            except socket.error as err:
                if err[0]==10013:
                    print('FATAL: cannot open TCP port {0}.'.format(kwargs['port']))
                    print('    Is another application running on that port?')
                else:
                    print(logError(err))
            except Exception as err:
                print(logError(err))
            print('    Trying again in {0} seconds'.format(RETRY_PERIOD))
            for _ in range(RETRY_PERIOD):
                time.sleep(1)
                print('.')
            print('')
