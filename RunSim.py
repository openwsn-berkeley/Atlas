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
    
    # create the Floorplan
    flootplan = Floorplan(simSetting['floorplanDrawing'])
    
    # create the DotBots
    dotBots = []
    for dotBotId in range(simSetting['numDotBots']):
        dotBots += [DotBot(dotBotId)]
    
    # drop the DotBots at their initial position
    for dotBot in dotBots:
        dotBot.setInitialPosition(simSetting['initialPosition'])
    
    # create the SimEngine
    simEngine = SimEngine(dotBots)

#============================ main ============================================

def main():
    for simSetting in SIMSETTINGS:
        oneSim(simSetting)

if __name__=='__main__':
    main()