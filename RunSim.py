import DotBot
import SimEngine

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
    floorplan      = Floorplan(simSetting['floorplanDrawing'])
    
    # create the DotBots
    dotBots        = []
    for dotBotId in range(simSetting['numDotBots']):
        dotBots   += [DotBot(dotBotId)]
    
    # drop the DotBots on the floorplan at their initial position
    for dotBot in dotBots:
        dotBot.setInitialPosition(simSetting['initialPosition'])
    
    # create the orchestrator
    orchestrator   = Orchestrator()
    
    # create the wireless communication between the DotBots and the orchestrator
    wireless       = Wireless()
    
    # create the SimEngine
    simEngine      = SimEngine(floorplan,dotBots)
    
    # start the UI
    simUI          = SimUI()

#============================ main ============================================

def main():
    for simSetting in SIMSETTINGS:
        oneSim(simSetting)

if __name__=='__main__':
    main()