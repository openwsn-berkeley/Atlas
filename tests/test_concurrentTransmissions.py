
import pytest
import random
import Wireless
import Orchestrator
import DotBot
# ============================ fixtures ==============================

EXPECTEDINOUT = [

    {
        'in': {
            'nodePdrs':   {
                'A': [1],
                'B': [0.90, 0.56, 0.36, 0.1575, 0.18],
                'C': [0.63, 0.405, 0.8, 0.225, 0.126],
                'D': [0.4725, 0.54, 0.336, 0.6, 0.3]
            },
            'movingNode': 'D'
        },

        'out': 0.9549
    },
    {
        'in': {
            'nodePdrs': {
                'A': [1],
                'B': [0.90, 0.56, 0.36, 0.1575, 0.18],
                'C': [0.63, 0.405, 0.8, 0.225, 0.126],
                'D': [0.4725, 0.54, 0.336, 0.6, 0.3]
            },
            'movingNode': 'C'
        },

        'out': 0.9702
    },
    {
        'in': {
            'nodePdrs': {
                'A': [1],
                'B': [0.90, 0.56, 0.36, 0.1575, 0.18],
                'C': [0.63, 0.405, 0.8, 0.225, 0.126],
                'D': [0.4725, 0.54, 0.336, 0.6, 0.3]
            },
            'movingNode': 'B'
        },

        'out': 0.9805
    },


]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_successProbabilityCT(expectedInOut):
    '''
    testing success probability given nodes and node total PDRs
    '''

    class TestWireless(Wireless.Wireless):

        def _computePdrPisterHack(self, sender_pos, receiver_pos):
            pdr = 0.7
            return pdr

    orchestrator = Orchestrator.Orchestrator(
        numRobots=4,
        initX=0,
        initY=0,
    )

    floorplan = '''
         ######
         #...s#
         ######
     '''

    dotBots = []
    x_pos = 0
    for dotBotId in range(1, 5):
        dotBots += [DotBot.DotBot(
            dotBotId=dotBotId,
            x=x_pos,
            y=0,
            floorplan=floorplan
        )]
        x_pos = x_pos + 100

    testwireless = TestWireless(pdrs=1)
    testwireless.indicateDevices(devices=dotBots + [orchestrator])
    print(testwireless._computePdrPisterHack(sender_pos=None, receiver_pos=None))
    dotBots[1].isRelay = True

    assert 1==2
