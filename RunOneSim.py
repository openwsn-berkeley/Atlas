# logging (do first)
import LoggingConfig
import logging
import logging.config
logging.config.dictConfig(LoggingConfig.LOGGINGCONFIG)

# built-in
import os
import argparse
import time
import random
import ast
# third-party
# local
import Floorplan
import DotBot
import Orchestrator
import Wireless
import SimEngine
import DataCollector

#====================================== HELPER =================================================

def runSim(simSetting, simUI):
    '''
    Run a single simulation. Finishes when map is complete (or mapping times out).
    '''

    # ======================== setup
    print("simulation started")
    
    # setting the seed
    random.seed(simSetting['seed'])
    
    # create the SimEngine
    simEngine      = SimEngine.SimEngine()

    # create the floorplan
    floorplan      = Floorplan.Floorplan(simSetting['floorplanDrawing'])

    # shorthand
    (initx, inity) = simSetting['initialPosition']

    # create the DotBots
    dotBots        = []
    for dotBotId in range(simSetting['numDotBots']):
        dotBots   += [DotBot.DotBot(dotBotId, initx, inity, floorplan)]

    # create the orchestrator
    orchestrator   = Orchestrator.Orchestrator(
        simSetting['numDotBots'],
        simSetting['initialPosition'],
        simSetting['navAlgorithm'],
        simSetting['relaySettings'],
        simSetting['config ID'],
    )

    # create the wireless communication medium
    wireless_model      = getattr(Wireless, f"Wireless{simSetting['wirelessModel']}")
    propagation_model   = getattr(Wireless, f"Propagation{simSetting['propagationModel']}")
    wireless            = wireless_model(propagation=propagation_model)
    wireless.indicateDevices(devices=dotBots + [orchestrator])
    wireless.indicateFloorplan(floorplan=floorplan)

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

    kpis = {
        'numDotBots':        simSetting['numDotBots'],
        'relaySettings':     simSetting['relaySettings'],
        'navAlgorithm':      simSetting['navAlgorithm'],
        'numRelays':         orchestrator.navigation.relayPositions,
        'timeToFullMapping': timeToFullMapping,
        'mappingProfile':    orchestrator.timeseries_kpis['numCells'], 'relayProfile': orchestrator.relayProfile,
        'pdrProfile':        orchestrator.timeseries_kpis['pdrProfile'],
        'timeline':          orchestrator.timeseries_kpis['time'], 'completion': simEngine.simComplete,
    }

    return kpis

#========================= main ==========================================

def main(simSetting, simUI=None):
    '''
    This function is called directly by RunSim when running standalone,
    and by the code below when running from CLEPS.
    '''
    
    # setup logging
    log            = logging.getLogger('RunOneSim')
    
    # log start of simulation
    log.info(f'simulation starting')
    
    # setup data collection
    dataCollector  = DataCollector.DataCollector()
    log_dir        = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    dataCollector.setFileName(
        os.path.join(
            log_dir,
            '{}_{}_{}.json'.format(
                simSetting['config ID'],
                time.strftime("%y%m%d%H%M%S", time.localtime()),
                simSetting['seed'],
            )
        )
    )
    
    # collect simSettings
    dataCollector.collect(
        {
            'type':       'simSetting',
            'simSetting': simSetting,
        },
    )
    
    # run the simulation (blocking)
    kpis = runSim(simSetting, simUI)

    # log outcome
    if kpis['completion']:
        log.info(
            "run {} completed in {}s with seed {}".format(
                simSetting['config ID'],
                kpis['timeToFullMapping'],
                simSetting['seed'],
            )
        )
    else:
        log.error(
            "run {} FAILED with seed {}".format(
                simSetting['config ID'],
                simSetting['seed'],
            )
        )

if __name__ == '__main__':
    '''
    Used by CLEPS only.
    '''
    
    parser         = argparse.ArgumentParser()
    parser.add_argument("--simSetting", help="A string containing a dictionary.")
    args           = parser.parse_args()
    
    # convert the simSetting parameter (a string) to a dictionnary
    simSetting     = eval(args.simSetting)
    assert type(simSetting)==dict
    
    main(simSetting)
