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
import Logging
import random
import ast
import traceback

from atlas.config import AtlasConfig

#====================================== HELPER =================================================

def runSim(simSetting, simUI):
    '''
    Run a single simulation. Finishes when map is complete (or mapping times out).
    '''

    random.seed(simSetting['seed'])

    # ======================== setup
    print("simulation started")
    # create the SimEngine
    simEngine = SimEngine.SimEngine()

    # create the floorplan
    floorplan = Floorplan.Floorplan(simSetting['floorplanDrawing'])

    # shorthand
    (initx, inity) = simSetting['initialPosition']

    # create the DotBots
    dotBots = []
    for dotBotId in range(simSetting['numDotBots']):
        dotBots += [DotBot.DotBot(dotBotId, initx, inity, floorplan)]

    # create the orchestrator
    orchestrator = Orchestrator.Orchestrator(
        simSetting['numDotBots'],
        simSetting['initialPosition'],
        simSetting['navAlgorithm'],
        simSetting['relaySettings'],
        simSetting['config ID'],
    )

    # create the wireless communication medium
    wireless_model = getattr(Wireless, f"Wireless{simSetting['wirelessModel']}")
    propagation_model = getattr(Wireless, f"Propagation{simSetting['propagationModel']}")

    wireless = wireless_model(propagation=propagation_model)
    wireless.indicateDevices(devices=dotBots + [orchestrator])
    wireless.indicateFloorplan(floorplan=floorplan)
    # wireless.overridePDR(simSetting['pdr'])

    # ======================== run

    # let the UI know about the new objects
    if simUI:
        simUI.updateObjectsToQuery(floorplan, dotBots, orchestrator)

    # if there is no UI, run as fast as possible
    if not simUI:
        simEngine.commandFastforward()

    # start a simulaion (blocks until done)
    timeToFullMapping = simEngine.runToCompletion(orchestrator.startExploration)



    # ======================== teardown

    # destroy singletons
    simEngine.destroy()
    wireless.destroy()

    kpis = {'numDotBots': simSetting['numDotBots'], 'numRelays': orchestrator.navigation.relayPositions,
            'timeToFullMapping': timeToFullMapping,
            'relaySettings': simSetting['relaySettings'], 'navAlgorithm': simSetting['navAlgorithm'],
            'mappingProfile': orchestrator.timeseries_kpis['numCells'], 'relayProfile': orchestrator.relayProfile,
            'pdrProfile': orchestrator.timeseries_kpis['pdrProfile'],
            'timeline': orchestrator.timeseries_kpis['time'], 'completion': simEngine.simComplete, }

    return kpis

#========================= MAIN ==========================================

def main(simSetting, simUI):
    
    # setup logging
    log            = logging.getLogger('RunOneSim')
    logger         = Logging.PeriodicFileLogger()
    log_dir        = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    log_filename   = f'{config_id}_{time.strftime("%y%m%d%H%M%S", time.localtime())}_{unique_id}.json'
    logger.setFileName(os.path.join(log_dir, log_filename))
    
    # log start of simulation
    log.info(f'simulation starting')
    
    if type(simUI) == str: # FIXME remove
        simUI = eval(simUI)
    
    if type(simSetting) == str:
        simSetting = ast.literal_eval(simSetting)
    
    unique_id = simSetting['seed']
    config_id = simSetting['config ID']

    # log
    config_data         = simSetting
    config_data["type"] = "sim configuration"
    seed = simSetting["seed"]
    logger.log(config_data)
    
    kpis = runSim(simSetting, simUI)

    #TODO: remove below, move to SimEngine
    if kpis['completion'] is True:
        time_to_full_mapping = kpis['timeToFullMapping']
        log.info(
            f"    run {config_id} completed in {time_to_full_mapping}s at {time.strftime('%H:%M:%S', time.localtime(time.time()))} with seed {seed} ")
    else:
        log.info(
            f"    run {config_id} failed at {time.strftime('%H:%M:%S', time.localtime(time.time()))} with seed {seed} ")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--simSetting", help="simulation configuration settings as dictionary")
    parser.add_argument("--simUI", default=None, help="UI configurations")

    args = parser.parse_args()
    simSetting = args.simSetting
    simUI = args.simUI

    main(simSetting, simUI)
