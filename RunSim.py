# logging (do first)
import os

import pkg_resources
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

from atlas.config import DefaultAtlasConfig

#============================ helpers =========================================

def runSim(simSetting, simUI):
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
        simSetting['relayAlg'],
    )
    
    # create the wireless communication medium
    wireless       = Wireless.WirelessBase()
    wireless.indicateDevices(devices = dotBots+[orchestrator])
    #wireless.overridePDR(simSetting['pdr'])
    
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

    return {'numDotBots': simSetting['numDotBots'], 'navAlgorithm': simSetting['navAlgorithm'],
            'pdr': None, 'timeToFullMapping': timeToFullMapping,
            'relayAlg': simSetting['relayAlg']}




#============================ main ============================================

# logging
log = logging.getLogger('RunSim')

def main(config):
    # ============================ defines =========================================
    SIMSETTINGS = []

    nav_config = config.orchestrator.navigation

    for idx, floorplan in enumerate(config.world.floorplans):
        for numrobot in config.world.robots.counts:
            for nav in nav_config.models:
                for relay in nav_config.relay.algorithms:
                    for path_planner in nav_config.path_planning.algorithms:
                        for target_selector in nav_config.target_selector.algorithms:
                            SIMSETTINGS.append(
                                {
                                    'numDotBots': numrobot,
                                    'floorplanType': idx,
                                    'floorplanDrawing': pkg_resources.resource_string('atlas.resources.maps',
                                                                                   floorplan).decode('utf-8'),
                                    'initialPosition': (1, 1),
                                    'navAlgorithm': nav,
                                    'pathPlanner': path_planner,
                                    'relayAlg': relay,
                                    'targetSelector': target_selector
                                },
                            )
    
    # log
    log.debug('simulation starting')
    
    # create the UI
    simUI          = SimUI.SimUI() if config.ui else None

    start_time = time.time()
    base_dir = "./logs"
    os.makedirs(base_dir, exist_ok=True)
    log_file = f'{config.experiment.logging.name}_{time.strftime("%y%m%d%H%M%S", time.localtime(start_time))}.json'

    # TODO: add timing bindings to relevant classes & functions
    with open(os.path.join(base_dir, log_file), 'a') as f:
        # run a number of simulations
        for (runNum, simSetting) in enumerate(SIMSETTINGS):
            # log
            log.info(f"run {runNum+1}/{len(SIMSETTINGS)} starting")
            kpis = runSim(simSetting,simUI)
            time_to_full_mapping = kpis['timeToFullMapping']
            log.info(f"    run {runNum+1}/{len(SIMSETTINGS)} completed in {time_to_full_mapping}s")
            kpis['runNums'] = runNum
            f.write(json.dumps(kpis) + '\n')
            f.flush()
    
    # block until user closes
    input('Press Enter to close simulation.')

if __name__=='__main__':
    # TODO: add optional
    config = DefaultAtlasConfig()
    main(config.atlas)
