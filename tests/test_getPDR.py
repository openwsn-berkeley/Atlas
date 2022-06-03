
import Wireless
import pytest
import DotBot
# ============================ fixtures ==============================

EXPECTEDINOUT = [

    {
        'in': {
            'linkStabilities': {
                ('A', 'B'): 0.80,
            },
            'sender':       'A',
            'receiver':     'B',
        },
        'out': 0.80
    },
    {
        'in': {
            'linkStabilities': {
                ('A', 'B'): 0.60,
                ('A', 'C'): 0.90,
                ('A', 'D'): 0.20,
                ('B', 'D'): 0.70,
                ('C', 'D'): 0.80,
            },
            'sender':       'A',
            'receiver':     'D',
        },
        'out': 0.87008
    },
    {
        'in': {
            'linkStabilities': {
                ('D', 'A'): 0.70,
                ('A', 'F'): 0.50,
                ('D', 'F'): 0.20,
                ('D', 'B'): 0.98,
                ('B', 'F'): 0.95,
                ('D', 'C'): 0.47,
                ('C', 'F'): 0.6,
            },
            'sender':   'D',
            'receiver': 'F',
        },
        'out': 0.97423816
    },
]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

class TestWireless(Wireless.Wireless):
    def __new__(cls, linkStabilities):
        return object.__new__(cls)

    def __init__(self, linkStabilities):
        super().__init__()
        self.linkStabilities = linkStabilities

    def _getStability(self, sender, receiver):
        return self.linkStabilities[(sender, receiver)]

def test_getPDR(expectedInOut):
    '''
    testing success probability of a packet going through to a moving node from a given
    root node given relays and link PDRs
    '''

    input         = expectedInOut['in']  # shorthand

    testwireless  = TestWireless(input['linkStabilities'])

    relays        = []
    relays       += [node[0] for node in input['linkStabilities'].keys()]
    relays       += [node[1] for node in input['linkStabilities'].keys()]
    relays        = list(set(relays))

    if relays:
        # if we have relays remove sender and receiver from that list
        relays.remove(input['sender'])
        relays.remove(input['receiver'])

    assert testwireless._getPDR(
        sender    =   input['sender'],
        receiver  =   input['receiver'],
        relays    =   relays
    ) == expectedInOut['out']

def test_getPDRReceiverIsRelay():
    '''
    testing success probability of a packet going through to a moving node from a given
    root node given relays and link PDRs
    '''

    wireless  = TestWireless({
        ('A', 'B'): 0.60,
        ('A', 'C'): 0.70,
        ('C', 'B'): 0.90,
    })

    assert wireless._getPDR(
        sender    =   'A',
        relays    =  ['B', 'C'],
        receiver  =   'B',

    ) == 0.852