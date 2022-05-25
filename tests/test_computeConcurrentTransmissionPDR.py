
import Wireless
import Orchestrator
import DotBot

# ============================ fixtures ==============================

# ============================ tests =================================

def test__computeConcurrentTransmissionPDR():
    '''
    testing PDR computation based on set distances
    '''

    orchestrator   = Orchestrator.Orchestrator(
        numRobots  = 4,
        initX      = 0,
        initY      = 0,
    )

    floorplan = '''
        ######
        #...s#
        ######
    '''

    dotBots        = []
    x_pos          = 0
    for dotBotId in range(1,5):
        dotBots += [DotBot.DotBot(
            dotBotId  = dotBotId,
            x         = x_pos,
            y         = 0,
            floorplan = floorplan
        )]
        x_pos = x_pos + 10


    wireless       = Wireless.Wireless()
    wireless.indicateDevices(devices=dotBots+[orchestrator])

    pdr_no_relay     = wireless._computeConcurrentTransmissionPDR(dotBots[0], dotBots[3])

    dotBots[1].relay = True

    pdr_one_relay    = wireless._computeConcurrentTransmissionPDR(dotBots[0], dotBots[3])

    dotBots[2].relay = True

    pdr_two_relays   = wireless._computeConcurrentTransmissionPDR(dotBots[0], dotBots[3])

    assert  0 <= pdr_no_relay   <= 1
    assert  0 <= pdr_one_relay  <= 1
    assert  0 <= pdr_two_relays <= 1