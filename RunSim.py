# logging (do first)
import AtlasLogging
import logging
import logging.config
logging.config.dictConfig(AtlasLogging.LOGGING_CONFIG)

# built-in
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
.#.............
......##.......
......##.......
..#...........#
''',
        'initialPosition'    :  (1,0),
        'navAlgorithm'       :  'Atlas',
        'pdr'                :  1,
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
        log.info('run %d/%d starting',runNum+1,len(SIMSETTINGS))
        timeToFullMapping = oneSim(simSetting,simUI)
        log.info('    run %d/%d completed in %d s',runNum+1,len(SIMSETTINGS),timeToFullMapping)
    
    # block until user closes
    input('Press Enter to close simulation.')

if __name__=='__main__':
    main()
