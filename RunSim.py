LOGGING_CONFIG = { 
    'version':                    1,
    'disable_existing_loggers':   True,
    'formatters': { 
        'formatter_console': { 
            #'format':             '%(message)s',
            'style':              '{',
            'format':             '{message}',
        },
        'formatter_file': {
            'style':              '{',
            'format':             '{asctime} [{levelname:>8}] {name:>12}: {message}',
        },
    },
    'handlers': { 
        'handler_console': { 
            'level':              'INFO',
            'formatter':          'formatter_console',
            'class':              'logging.StreamHandler',
        },
        'handler_file': {
            'level':              'DEBUG',
            'formatter':          'formatter_file',
            'class':              'logging.handlers.RotatingFileHandler',
            'filename':           'Atlas.log',
            'maxBytes':           1000000,
            'backupCount':        10
        },
    },
    'loggers': { 
        '': { # root
            'handlers':           ['handler_console','handler_file'],
            'level':              'DEBUG',
            'propagate':          False
        },
        'RunSim': { 
            'handlers':           ['handler_console','handler_file'],
            'level':              'DEBUG',
            'propagate':          False
        },
        'Orchestrator': { 
            'handlers':           ['handler_console','handler_file'],
            'level':              'DEBUG',
            'propagate':          False
        },
        'DotBot': { 
            'handlers':           ['handler_console','handler_file'],
            'level':              'DEBUG',
            'propagate':          False
        },
    } 
}

# built-in
import logging
import logging.config
logging.config.dictConfig(LOGGING_CONFIG)
# third-party
# local
import Floorplan
import DotBot
import Orchestrator
import Wireless
import SimEngine
import SimUI


#============================ defines =========================================

UI_ACTIVE     = True

SIMSETTINGS   = [
    {
        'numDotBots'         : 1,
        'floorplanDrawing'   : # 1m per character
 '''
...............
...............
...............
...............
''',
        'initialPosition'    :  (1,1),
        'navAlgorithm'       :  'Ballistic',
        'pdr'                :  0.5,
    }
]

#============================ helpers =========================================

def oneSim(simSetting,simUI):
    '''
    Run a single simulation. Finishes when map is complete (or mapping times out).
    '''
    
    #======================== setup
    
    # create the SimEngine
    simEngine      = SimEngine.SimEngine()
    
    # create the floorplan
    floorplan      = Floorplan.Floorplan(simSetting['floorplanDrawing'])
    
    # shorthand
    (initx,inity)  = simSetting['initialPosition']
    
    # create the DotBots
    dotBots        = []
    for dotBotId in range(simSetting['numDotBots']):
        dotBots   += [DotBot.DotBot(dotBotId,initx,inity,floorplan)]
    
    # create the orchestrator
    orchestrator   = Orchestrator.Orchestrator(
        simSetting['numDotBots'],
        simSetting['initialPosition'],
        simSetting['navAlgorithm'],
    )
    
    # create the wireless communication medium
    wireless       = Wireless.Wireless()
    wireless.indicateDevices(devices = dotBots+[orchestrator])
    wireless.overridePDR(simSetting['pdr'])
    
    #======================== run
    
    # let the UI know about the new objects
    if simUI:
        simUI.updateObjectsToQuery(floorplan,dotBots,orchestrator)
    
    # if there is no UI, run as fast as possible
    if not simUI:
       simEngine.commandFastforward()
    
    # start a simulaion (blocks until done)
    timeToFullMapping = simEngine.runToCompletion(orchestrator.startExploration)
    
    #======================== teardown

    # destroy singletons
    simEngine.destroy()
    wireless.destroy()
    
    return timeToFullMapping

#============================ main ============================================

# logging
log = logging.getLogger('RunSim')

def main():
    
    # log
    log.debug('simulation starting')
    
    # create the UI
    if UI_ACTIVE:
        simUI          = SimUI.SimUI()
    else:
        simUI          = None
    
    # run a number of simulations
    for (runNum,simSetting) in enumerate(SIMSETTINGS):
        # log
        log.info('run {:>3}/{} starting'.format(runNum+1,len(SIMSETTINGS)))
        timeToFullMapping = oneSim(simSetting,simUI)
        log.info('    run {:>3}/{} completed in {:>7} s'.format(runNum+1,len(SIMSETTINGS),timeToFullMapping))
    
    # block until user closes
    input('Press Enter to close simulation.')

if __name__=='__main__':
    main()
