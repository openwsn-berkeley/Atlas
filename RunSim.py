# built-in
# third-party
import csv
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
        'numDotBots':       20,
        'floorplanDrawing': # 1m per character
'''
............###...
..................
....##.....##.....
....##............
..............##..
..............##..
''',
        'initialPosition':  (5,1),
        'orchLocation'   :  (5,1),
        'navAlgorithm'   :   'Ballistic', #set navigation algorithm. options are: 1. Ballistic 2. Atlas_2.0
    }

]
#============================ helpers =========================================

def oneSim(simSetting):
    '''
    Run a single simulation.
    '''
    currentRun = 1
    # create the wireless communication
    wireless       = Wireless.Wireless()
    
    # create the SimEngine
    simEngine      = SimEngine.SimEngine()
    
    # create the floorplan
    floorplan      = Floorplan.Floorplan(simSetting['floorplanDrawing'])
    
    # create the DotBots
    dotBots        = []
    for dotBotId in range(simSetting['numDotBots']):
        dotBots   += [DotBot.DotBot(dotBotId,floorplan)]
    
    # drop the DotBots on the floorplan at their initial position
    (x,y) = simSetting['initialPosition']
    for dotBot in dotBots:
        dotBot.setInitialPosition(x,y)


    #set orchestrator position
    (xo,yo) = simSetting['orchLocation']
    wireless.indicateOrchLocation(xo,yo)

    # create the orchestrator
    orchestrator   = Orchestrator.Orchestrator([simSetting['initialPosition']]*len(dotBots),floorplan)
    
    # indicate the elements to the singletons
    wireless.indicateElements(dotBots,orchestrator)
    
    # start the UI (call last)
    #simUI          = SimUI.SimUI(floorplan,dotBots,orchestrator)

    orchestrator.setNavAlgorithm([simSetting['navAlgorithm']])

    # schedule the first event
    simEngine.schedule(0,orchestrator.startExploration)

    for dotBot in dotBots:
        dotBot.wakeBot()

    simEngine.commandPlay(20.00)

    with open('DotBot.csv', 'w', newline = '') as f:
        writer = csv.writer(f)
        writer.writerow(["simRun", "PDR", "numRobots","timeToComplete (seconds)"])
        while True:
            if orchestrator.mapBuilder.simRun >= 1000:
                exit()
            if orchestrator.mapBuilder.simRun > currentRun:
                #do all the re-initializing here
                print('========================RESET===============================')
                kpis = {'numRobots':simSetting['numDotBots'],
                        'timeToComplete':simEngine.timeToCompleation(),
                        'PDR':wireless.PDR,
                        'simRun': currentRun,
                        }
                writer.writerow([kpis['simRun'], kpis['PDR'], kpis['numRobots'], kpis['timeToComplete']])
                #f.write(str(kpis)+'\n')
                f.flush()
                #set PDR value for next run
                if orchestrator.mapBuilder.simRun in range(0,100):
                    pdr = 1
                if orchestrator.mapBuilder.simRun in range(100,200):
                    pdr = 0.9
                if orchestrator.mapBuilder.simRun in range(200,300):
                    pdr = 0.8
                if orchestrator.mapBuilder.simRun in range(300,400):
                    pdr = 0.7
                if orchestrator.mapBuilder.simRun in range(400,500):
                    pdr = 0.6
                if orchestrator.mapBuilder.simRun in range(500,600):
                    pdr = 0.5
                if orchestrator.mapBuilder.simRun in range(600,700):
                    pdr = 0.4
                if orchestrator.mapBuilder.simRun in range(700,800):
                    pdr = 0.3
                if orchestrator.mapBuilder.simRun in range(800,900):
                    pdr = 0.2
                if orchestrator.mapBuilder.simRun in range(900,1000):
                    pdr = 0.1

                # reset simEngine
                simEngine.reset()

                #reset wireless
                wireless.reset(pdr)

                # reset robots
                for dotBot in dotBots:
                    dotBot.reset()

                # send robots back to starting position
                (x, y) = simSetting['initialPosition']
                for dotBot in dotBots:
                    dotBot.setInitialPosition(x, y)

                #reset mapbuilder
                orchestrator.mapBuilder.reset()

                # set orchestrator position
                (xo, yo) = simSetting['orchLocation']
                wireless.indicateOrchLocation(xo, yo)

                print('current time', simEngine.currentTime())

                # schedule first event for new simulation run
                simEngine.schedule(0, orchestrator.startExploration)

                # reset orchestrator
                orchestrator.reset()

                # wake dotbots up to start checking packets
                for dotBot in dotBots:
                    dotBot.wakeBot()

                #increement current run
                currentRun = orchestrator.mapBuilder.simRun

                simEngine.commandPlay(20.00)


    input('Press Enter to close simulation.')

#============================ main ============================================

def main():
    for simSetting in SIMSETTINGS:
        oneSim(simSetting)

if __name__=='__main__':
    main()
