
import pytest
import random
import Wireless
import DotBot

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # two close positions ( <1 m apart)
    {
        'in': {
            'sender':     DotBot.DotBot(dotBotId=1,x=0.00, y=0.00,floorplan='#'),
            'receiver':   DotBot.DotBot(dotBotId=1,x=0.00, y=0.50,floorplan='#')
        },

        'out': 1.00
    },

    # two out of range positions (1000 m)
    {
        'in': {
            'sender':   DotBot.DotBot(dotBotId=1,x=0.00, y=0.00,floorplan='#'),
            'receiver': DotBot.DotBot(dotBotId=1,x=0.00, y=1000.00,floorplan='#'),
        },

        'out': 0.00
    },
]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

RANDOMPOSITIONS = [{
    'sender':   DotBot.DotBot(dotBotId=1,x=random.uniform(0.00, 1000.00), y=random.uniform(0.00, 1000.00),floorplan='#'),
    'receiver': DotBot.DotBot(dotBotId=1,x=random.uniform(0.00, 1000.00), y=random.uniform(0.00, 1000.00),floorplan='#'),
    }
    for i in range(1000)
]

@pytest.fixture(params=RANDOMPOSITIONS)
def randomPositions(request):
    return request.param

#============================ tests =================================

def test_computePdrPisterHack(expectedInOut):
    '''
    testing PDR computation based on set distances
    '''

    wireless = Wireless.Wireless()

    assert wireless._getStability(*expectedInOut['in'].values()) == expectedInOut['out']


def test_getStabilityRandomPositions(randomPositions):
    '''
    testing PDR computation based on random distances
    '''

    wireless = Wireless.Wireless()

    # friis pdr
    wireless.PISTER_HACK_LOWER_SHIFT = 0
    pdr_friis = wireless._getStability(*randomPositions.values())

    # pister hack pdr
    wireless.PISTER_HACK_LOWER_SHIFT = 40
    pdr_pisterHack = wireless._getStability(*randomPositions.values())

    assert 0 <= pdr_pisterHack <= 1
    assert pdr_pisterHack <= pdr_friis

def test_getStabilitySamePositions():
    '''
    testing that getStability() always returns same PDR if sender and receiver
    are in the same positions as last time PDR was computed
    '''

    wireless = Wireless.Wireless()
    sender   = DotBot.DotBot(dotBotId=1, x=0, y=0, floorplan='#')
    receiver = DotBot.DotBot(dotBotId=2, x=10, y=10, floorplan='#')

    pdr1     = wireless._getStability(sender, receiver)
    pdr2     = wireless._getStability(sender, receiver)

    assert pdr1 == pdr2

    (receiver.x, receiver.y) = (50,50)
    pdr3                     = wireless._getStability(sender, receiver)

    assert pdr3 != pdr2

