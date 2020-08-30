# built-in
import threading
import webbrowser
# third-party
import bottle
# local
import SimVersion

class SimUI(object):
    '''
    Web-based User Interface of the simulator.
    '''
    
    TCPPORT = 8080
    
    def __init__(self):
    
        # start web server
        self.websrv   = bottle.Bottle()
        self.websrv.route('/',                        'GET',    self._webhandle_root_GET)
        self.websrv.route('/static/<filename>',       'GET',    self._webhandle_static_GET)
        self.websrv.route('/floorplan.json',          'GET',    self._webhandle_floorplan_GET)
        self.websrv.route('/robotpositions.json',     'GET',    self._webhandle_robotpositions_GET)
        self.websrv.route('/play',                    'POST',   self._webhandle_play_POST)
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
    
    #======================== private =========================================
    
    #=== web handles
    
    def _webhandle_root_GET(self):
        return bottle.template(
            'SimUI',
            pagetitle   = 'DotBotSim',
            version     = SimVersion.formatVersion(),
        )
    
    def _webhandle_static_GET(self,filename):
        return bottle.static_file(filename, root='static/')
    
    def _webhandle_floorplan_GET(self):
        print('TODO floorplan')
        return {'message': 'TODO floorplan'}
    
    def _webhandle_robotpositions_GET(self):
        print('TODO robotpositions')
        return {'message': 'TODO robotpositions'}
        
    def _webhandle_play_POST(self):
        print('TODO play')
    
    def _webhandle_pause_POST(self):
        print('TODO pause')
    
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