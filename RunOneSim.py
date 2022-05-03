# built-in
import argparse
import random
import json
# third-party
# local
import Floorplan
import DotBot
import Orchestrator
import Wireless
import SimEngine
import DataCollector
import Utils as u
# setup logging
import logging.config
log = logging.getLogger('RunOneSim')

#====================================== HELPER =================================================

def runOneSim(simSetting, simUI=None):
    '''
    Run a single simulation. Finishes when map is complete (or mapping times out).
    '''

    # ======================== setup

    # set up logfile name for this run
    u.setLoggerUname(simSetting['uname'])

    # log
    log.info('Simulation started')

    # setup data collection
    dataCollector = DataCollector.DataCollector()
    dataCollector.setUname(simSetting['uname'])

    # collect simSettings
    dataCollector.collect(
        {
            'type':         'simSetting',
            'simSetting':   simSetting,
        },
    )

    # setting the seed
    random.seed(simSetting['seed'])
    
    # create the SimEngine
    simEngine      = SimEngine.SimEngine()

    # create the floorplan
    floorplan      = Floorplan.Floorplan(simSetting['floorplan'])

    # shorthand
    (initx, inity) = (simSetting['initialPositionX'], simSetting['initialPositionY'])

    # create the DotBots
    dotBots        = []
    for dotBotId in range(simSetting['numRobots']):
        dotBots   += [DotBot.DotBot(dotBotId, initx, inity, floorplan)]

    # create the orchestrator
    relaySettings = {
        "relayAlgorithm":    simSetting['relayAlgorithm'],
        "lowerPdrThreshold": simSetting['lowerPdrThreshold'],
        "upperPdrThreshold": simSetting['upperPdrThreshold'],
        }
    orchestrator   = Orchestrator.Orchestrator(
        simSetting['numRobots'],
        (simSetting['initialPositionX'],simSetting['initialPositionY']),
        relaySettings,
        simSetting['navigationAlgorithm'],
    )

    # create the wireless communication medium

    wireless=Wireless.WirelessConcurrentTransmission()
    wireless.indicateDevices(devices=dotBots + [orchestrator])
    wireless.indicateFloorplan(floorplan=floorplan)

    # ======================== run

    # let the UI know about the new objects
    if simUI:
        simUI.updateObjectsToQuery(floorplan, dotBots, orchestrator)

    # if there is no UI, run as fast as possible
    if not simUI:
        simEngine.commandFastforward()

    # start a simulation (blocks until done)
    simEngine.runToCompletion(orchestrator.startExploration)

    # ======================== teardown

    # destroy singletons
    simEngine.destroy()
    wireless.destroy()


#========================= main ==========================================

def main(simSetting, simUI=None):
    '''
    This function is called directly by RunSim when running standalone,
    and by the code below when running from CLEPS.
    '''

    log.info('running on cleps ...')
    
    # run the simulation (blocking)
    runOneSim(simSetting, simUI)


if __name__ == '__main__':
    '''
    Used by CLEPS only.
    '''
    
    parser         = argparse.ArgumentParser()
    parser.add_argument("--simSetting", help="A string containing a dictionary.")
    args           = parser.parse_args()
    
    # convert the simSetting parameter (a string) to a dictionary
    simSetting     = json.loads(args.simSetting)

    main(simSetting)
