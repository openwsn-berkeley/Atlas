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
import time
import json


#============================ defines =========================================

UI_ACTIVE     = False

# FLOORPLANS    = [
# '''
# ################################################################################
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# ################################################################################
# ''',
#
# '''
# ################################################################################
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..........##....................##################################............#
# #..........##....................##################################............#
# #..........##..................................................................#
# #..........##..................................................................#
# #..........##..................................................................#
# #..........##..................................................................#
# #..........##..................................................................#
# #..........##..................................................................#
# #..........##..................................................................#
# #..........##..................................................................#
# #..........##....................##################################............#
# #..........##....................##################################............#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# #..............................................................................#
# ################################################################################
# ''',
#
# '''
# ################################################################################
# #..........#............#............#.....................#............#......#
# #..........#............#............#.....................#............#......#
# #..........#............#............#.....................#............#......#
# #..........#............#............#.....................#............#......#
# #..........#............#............#.....................#............#......#
# #.....##..###...##########..############..###################...##########..####
# #######........................................................................#
# #.....#........................................................................#
# #..............................................................................#
# #.....#........................................................................#
# #######...........#########..#############..#################..................#
# #.....#........................................................................#
# #..............................................................................#
# #.....#........................................................................#
# #######........................................................................#
# #.....##..###...##########..############..###################...##########..####
# #..........#............#............#.....................#............#......#
# #..........#............#............#.....................#............#......#
# #..........#............#............#.....................#............#......#
# #..........#............#............#.....................#............#......#
# #..........#............#............#.....................#............#......#
# ################################################################################
# '''
# ]

FLOORPLANS   = [

'''
##################
#................#
#................#
#................#
#................#
##################
''',

'''
##################
#................#
#...##.....##....#
#...##...........#
#.............####
##################
''',


]

PDRS          = [1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]

SIMSETTINGS   = []

for (idx,floorplan) in enumerate(FLOORPLANS):
    for pdr in PDRS:

        SIMSETTINGS   += [
            {
                'numDotBots'         : 50,
                'floorplanType'       : idx ,
                'floorplanDrawing'   : floorplan,
                'initialPosition'    :  (2,2),
                'navAlgorithm'       :  'Atlas',
                'pdr'                :  pdr,
            },
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

    return {'numDotBots': simSetting['numDotBots'],'navAlgorithm': simSetting['navAlgorithm'],
            'pdr': simSetting['pdr'], 'timeToFullMapping': timeToFullMapping,
            'floorplanType': simSetting['floorplanType'], 'floorplanDrawing': orchestrator.navigation.getHeatmap()[1],
            'heatmap': orchestrator.navigation.getHeatmap()[0], 'profile': orchestrator.navigation.getProfile()}

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

    startTime = time.time()
    with open('Atlas_kpi_Log_{0}.json'.format(time.strftime("%y%m%d%H%M%S", time.localtime(startTime))).format(), 'a') as f:
        # run a number of simulations
        for (runNum,simSetting) in enumerate(SIMSETTINGS):
            # log
            log.info('run %d/%d starting',runNum+1,len(SIMSETTINGS))
            kpis = oneSim(simSetting,simUI)
            timeToFullMapping = kpis['timeToFullMapping']
            log.info('    run %d/%d completed in %d s',runNum+1,len(SIMSETTINGS),timeToFullMapping)
            kpis['runNums'] = runNum
            f.write(json.dumps(kpis) + '\n')
            f.flush()
    
    # block until user closes
    input('Press Enter to close simulation.')

if __name__=='__main__':
    main()
