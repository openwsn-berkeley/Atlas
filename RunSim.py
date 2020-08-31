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

SIMSETTINGS = [
    {
        'numDotBots':       10,
        'floorplanDrawing': # 1m per character
'''
#############################
#                           #
#                           #
#                           #
#     ######                #
#                           #
#############################
''',
        'initialPosition':  (24,3),
    }
]

#============================ helpers =========================================

def oneSim(simSetting):
    '''
    Run a single simulation.
    '''
    
    # create the wireless communication
    wireless       = Wireless.Wireless()
    
    # create the SimEngine
    simEngine      = SimEngine.SimEngine()
    
    # create the floorplan
    floorplan      = Floorplan.Floorplan(simSetting['floorplanDrawing'])
    
    # create the DotBots
    dotBots        = []
    for dotBotId in range(simSetting['numDotBots']):
        dotBots   += [DotBot.DotBot(dotBotId)]
    
    # drop the DotBots on the floorplan at their initial position
    (x,y) = simSetting['initialPosition']
    for dotBot in dotBots:
        dotBot.setInitialPosition(x,y)
    
    # create the orchestrator
    orchestrator   = Orchestrator.Orchestrator([simSetting['initialPosition']]*len(dotBots))
    
    # indicate the elements to the singletons
    wireless.indicateElements(dotBots,orchestrator)
    
    # start the UI (call last)
    simUI          = SimUI.SimUI(floorplan,dotBots)
    
    # schedule the first event
    simEngine.schedule(0,orchestrator.startExploration)
    
    input('Press Enter to close simulation.')

#============================ main ============================================

def main():
    for simSetting in SIMSETTINGS:
        oneSim(simSetting)

if __name__=='__main__':
    main()
