# built-in
# third-party
import csv
import time
# local
import Floorplan
import DotBot
import Orchestrator
import Wireless
import SimEngine
import SimUI

#============================ defines =========================================

SIMSETTINGS = [
    {
        'numDotBots':       1,
        'floorplanDrawing': # 1m per character
 '''
.....................
.....................
''',
        'initialPosition':  (1,1),
        'navAlgorithm'   :  'Ballistic',
        'pdr'            :  1,
    },
    {
        'numDotBots':       1,
        'floorplanDrawing': # 1m per character
 '''
.....................
.....................
''',
        'initialPosition':  (1,1),
        'navAlgorithm'   :  'Ballistic',
        'pdr'            :  1,
    }
]

#============================ helpers =========================================

def oneSim(simSetting,simUI):
    '''
    Run a single simulation. Finishes when map is complete (or mapping times out).
    '''
    
    #======================== setup
    
    # create the wireless communication medium
    wireless       = Wireless.Wireless()
    
    # create the SimEngine
    simEngine      = SimEngine.SimEngine()
    
    # create the floorplan
    floorplan      = Floorplan.Floorplan(simSetting['floorplanDrawing'])
    
    # create the DotBots
    dotBots        = []
    for dotBotId in range(simSetting['numDotBots']):
        dotBots   += [DotBot.DotBot(dotBotId,floorplan)]
    
    # position the DotBots
    (initx,inity)  = simSetting['initialPosition']
    for dotBot in dotBots:
        dotBot.setInitialPosition(initx,inity)
    
    # create the orchestrator
    orchestrator   = Orchestrator.Orchestrator([simSetting['initialPosition']]*len(dotBots),floorplan)
    orchestrator.setNavAlgorithm([simSetting['navAlgorithm']])
    
    # position the Orchestrator
    wireless.indicateOrchLocation(initx,inity) # FIXME: position in Orchestrator
    
    # indicate the elements to the singletons
    wireless.indicateElements(dotBots,orchestrator) # FIXME: wireless only knows about devices
    
    #======================== run
    
    # let the UI know about the new objects
    simUI.updateObjectsToQuery(floorplan,dotBots,orchestrator)
    
    # start a simulaion (blocks until done)
    simEngine.runToCompletion(orchestrator.startExploration)
    
    #======================== teardown

    # destroy singletons
    simEngine.destroy()
    wireless.destroy()

#============================ main ============================================

def main():

    # create the UI
    simUI          = SimUI.SimUI()
    
    # run a number of simulations
    for (runNum,simSetting) in enumerate(SIMSETTINGS):
        print('run {}/{}...'.format(runNum+1,len(SIMSETTINGS)))
        oneSim(simSetting,simUI)
    
    # block until user closes
    input('Press Enter to close simulation.')

if __name__=='__main__':
    main()
