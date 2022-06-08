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

def runOneSim(simSetting, atlasUI=None):
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
    
    # create the simulation environment
    floorplan      = Floorplan.Floorplan(alias=simSetting['floorplan'])
    (initX, initY) = floorplan.getInitialPosition()
    simEngine      = SimEngine.SimEngine()
    orchestrator   = Orchestrator.Orchestrator(
        simSetting['numRobots'],
        initX,
        initY,
    )
    dotBots        = [
        DotBot.DotBot(dotBotId, initX, initY, floorplan)
        for dotBotId in range(1,simSetting['numRobots']+1)
    ]
    wireless       = Wireless.Wireless()
    wireless.indicateDevices(devices=dotBots+[orchestrator])

    # ======================== run

    # let the UI know about the new objects
    if atlasUI:
        atlasUI.updateObjectsToQuery(floorplan, dotBots, orchestrator)

    # if there is no UI, run as fast as possible
    if not atlasUI:
        simEngine.commandFastforward()

    # start a simulation (blocks until done)
    simEngine.runToCompletion(orchestrator.startExploration)

    # ======================== teardown

    # destroy singletons
    simEngine.destroy()
    wireless.destroy()


#========================= main ==========================================

def main(simSetting, atlasUI=None):
    '''
    This function is called directly by RunSim when running standalone,
    and by the code below when running from CLEPS.
    '''

    log.info('running on CLEPS, seed={}...'.format(simSetting['seed']))
    
    # run the simulation (blocking)
    runOneSim(simSetting, atlasUI)

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
