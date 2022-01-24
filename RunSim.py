# logging (do first)
import os
import argparse

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

from atlas.config import AtlasConfig

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
    wireless_model = getattr(Wireless, f"Wireless{simSetting['wirelessModel']}")
    propagation_model = getattr(Wireless, f"Propagation{simSetting['propagationModel']}")

    wireless       = wireless_model(propagation=propagation_model)
    wireless.indicateDevices(devices=dotBots+[orchestrator])
    wireless.indicateFloorplan(floorplan=floorplan)
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

    return {'numDotBots': simSetting['numDotBots'], 'numRelays': orchestrator.navigation.relayPositions,
            'timeToFullMapping': timeToFullMapping,
            'relayAlg': simSetting['relayAlg'], 'navAlgorithm': simSetting['navAlgorithm'],
            'mappingProfile': orchestrator.mappingProfile, 'relayProfile': orchestrator.relayProfile,
            'pdrProfile': orchestrator.pdrProfile,
            'timeline': orchestrator.timeline}




#============================ main ============================================

# logging
log = logging.getLogger('RunSim')

def main(config):
    # ============================ defines =========================================
    SIMSETTINGS = []

    nav_config = config.orchestrator.navigation

    # TODO: SimSettings should handle lack of certain parameters given a different configuration and maintains parameter cross product functionality
    # TODO: Have a validate configuration script that does an import dry run of all the configuration settings
    for idx, floorplan in enumerate(config.world.floorplans):
        for numrobot in config.world.robots.counts:
            for init_pos in config.world.robots.initial_positions:
                for wireless in config.wireless.models:
                    for propagation in config.wireless.propagation.models:
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
                                                'initialPosition': tuple(init_pos),
                                                'navAlgorithm': nav,
                                                'pathPlanner': path_planner,
                                                'relayAlg': relay,
                                                'targetSelector': target_selector,
                                                'wirelessModel': wireless,
                                                'propagationModel': propagation
                                            },
                                        )
    
    # log
    log.debug('simulation starting')
    
    # create the UI
    simUI          = SimUI.SimUI() if config.ui else None

    start_time = time.time()
    base_dir = "./logs"
    os.makedirs(base_dir, exist_ok=True)
    if config.cleps:
        log_file = f'{os.environ["SLURM_JOBID"]}_{os.environ["SLURM_NODEID"]}_{time.strftime("%y%m%d%H%M%S", time.localtime(start_time))}.json'
    else:
        log_file = f'{config.experiment.logging.name}_{time.strftime("%y%m%d%H%M%S", time.localtime(start_time))}.json'

    # TODO: add timing bindings to relevant classes & functions
    with open(os.path.join(base_dir, log_file), 'a') as f:
        # run a number of simulations
        for (runNum, simSetting) in enumerate(SIMSETTINGS):
            # log
            log.info(f"run {runNum+1}/{len(SIMSETTINGS)} starting")
            kpis = runSim(simSetting,simUI) # TODO: dump sim settings object alongside log (should be in results format)
            time_to_full_mapping = kpis['timeToFullMapping']
            log.info(f"    run {runNum+1}/{len(SIMSETTINGS)} completed in {time_to_full_mapping}s")
            kpis['runNums'] = runNum
            f.write(json.dumps(kpis) + '\n')
            f.flush()
    
    # block until user closes
    #input('Press Enter to close simulation.')

if __name__=='__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--config", type=str, default="default", help="Atlas configuration file name to use (must be TOML)")

    args = parser.parse_args()

    config = AtlasConfig(args.config)
    main(config.atlas)
