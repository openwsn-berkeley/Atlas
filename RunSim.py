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
        'numDotBots':       5,
        'floorplanDrawing': # 1m per character
 '''
...............
...............
#..............
...............
''',
        'initialPosition':  (1,1),
        'navAlgorithm'   :  'Ballistic',
        'pdr'            :  0.5,
    }
] * 10

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

def main():

    # create the UI
    if UI_ACTIVE:
        simUI          = SimUI.SimUI()
    else:
        simUI          = None
    
    # run a number of simulations
    for (runNum,simSetting) in enumerate(SIMSETTINGS):
        print('run {:>3}/{}...'.format(runNum+1,len(SIMSETTINGS)),end='')
        timeToFullMapping = oneSim(simSetting,simUI)
        print(' completed in {:>7} s'.format(timeToFullMapping))
    
    # block until user closes
    input('Press Enter to close simulation.')

if __name__=='__main__':
    main()
