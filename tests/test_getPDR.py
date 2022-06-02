
import Wireless
import pytest

# ============================ fixtures ==============================
EXPECTEDINOUT = [

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

    testwireless = TestWireless(expectedInOut['in']['linkStabilities'])

    assert testwireless._getPDR(
        sender    =   expectedInOut['in']['sender'],
        receiver  =   expectedInOut['in']['receiver'],
        relays    =   [node[0] for node in expectedInOut['in']['linkStabilities'].keys() if node[0] != expectedInOut['in']['sender']]
    ) == expectedInOut['out']

