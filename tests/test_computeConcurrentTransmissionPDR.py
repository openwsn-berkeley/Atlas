import Wireless
import Orchestrator
import DotBot

# ============================ fixtures ==============================

# ============================ tests =================================

def test_concurrentTransmission_addingRelays():
    '''
    testing Concurrent Transmission with various numbers of relays
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
        x_pos = x_pos + 100


    wireless       = Wireless.Wireless()
    wireless.indicateDevices(devices=dotBots+[orchestrator])

    # eliminate randomness (use Friis RSSI values) to ensure CT is working correctly
    wireless.PISTER_HACK_LOWER_SHIFT = 0

    pdr_no_relay     = wireless._computeConcurrentTransmissionPDR(dotBots[0], dotBots[3])
    assert round(pdr_no_relay, 2)  == 0.86

    dotBots[1].relay = True

    pdr_one_relay    = wireless._computeConcurrentTransmissionPDR(dotBots[0], dotBots[3])
    assert round(pdr_one_relay, 2) == 0.99

    dotBots[2].relay = True

    pdr_two_relays   = wireless._computeConcurrentTransmissionPDR(dotBots[0], dotBots[3])
    assert round(pdr_two_relays, 2) == 1.00

def test_concurrentTransmission_differentDistances():
    '''
    testing Concurrent Transmission with different distances between nodes
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
    x_positions    = [0, 265, 450, 700]

    for idx in range(1,5):
        dotBots += [DotBot.DotBot(
            dotBotId  = idx,
            x         = x_positions[idx-1],
            y         = 0,
            floorplan = floorplan
        )]


    wireless       = Wireless.Wireless()
    wireless.indicateDevices(devices=dotBots+[orchestrator])

    # eliminate randomness (use Friis RSSI values) to ensure CT is working correctly
    wireless.PISTER_HACK_LOWER_SHIFT = 0

    pdr_no_relay     = wireless._computeConcurrentTransmissionPDR(dotBots[0], dotBots[3])

    dotBots[1].relay = True
    dotBots[2].relay = True

    pdr_two_relays   = wireless._computeConcurrentTransmissionPDR(dotBots[0], dotBots[3])

    assert pdr_no_relay < pdr_two_relays