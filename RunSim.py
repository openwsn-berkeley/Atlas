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
        'numDotBots':       1,
        'floorplanDrawing': # 1m per character
'''
########################
#                      #
#                      #
#                      #
#                      #
#                      #
########################
''',
        'initialPosition':  (24,3),
    }
]

#============================ helpers =========================================

def oneSim(simSetting):
    '''
    Run a single simulation.
    '''
    
    # create the floorplan
    floorplan      = Floorplan.Floorplan(simSetting['floorplanDrawing'])
    
    # create the DotBots
    dotBots        = []
    for dotBotId in range(simSetting['numDotBots']):
        dotBots   += [DotBot.DotBot(dotBotId)]
    
    # drop the DotBots on the floorplan at their initial position
    for dotBot in dotBots:
        dotBot.setInitialPosition(simSetting['initialPosition'])
    
    # create the orchestrator
    orchestrator   = Orchestrator.Orchestrator()
    
    # create the wireless communication between the DotBots and the orchestrator
    wireless       = Wireless.Wireless()
    
    # create the SimEngine
    simEngine      = SimEngine.SimEngine(floorplan,dotBots)
    
    # start the UI (call last)
    simUI          = SimUI.SimUI()
    
    input('Press Enter to close simulation.')

#============================ main ============================================

def main():
    for simSetting in SIMSETTINGS:
        oneSim(simSetting)

if __name__=='__main__':
    main()
