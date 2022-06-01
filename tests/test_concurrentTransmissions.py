import Wireless
import pytest
# ============================ fixtures ==============================
EXPECTEDINOUT = [

    {
        'in': {
            'relays':      ['B', 'C'],
            'movingNode': 'D'
        },
        'out': 0.9549
    },
    {
        'in': {
            'relays': ['B', 'D'],
            'movingNode': 'C'
        },
        'out': 0.9702
    },
    {
        'in': {
            'relays': ['C', 'D'],
            'movingNode': 'B'
        },
        'out': 0.9805
    },
]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param
# ============================ tests =================================

class TestWireless(Wireless.Wireless):
    def __new__(cls):
        return object.__new__(cls)

    def _computePdrPisterHack(self, sender, receiver):
        pdrs = {
            ('A','B'): 0.90,
            ('A','C'): 0.80,
            ('A','D'): 0.30,
            ('B','A'): 0.90,
            ('B','C'): 0.70,
            ('B','D'): 0.60,
            ('C','A'): 0.80,
            ('C','B'): 0.70,
            ('C','D'): 0.75,
            ('D','A'): 0.30,
            ('D','B'): 0.60,
            ('D','C'): 0.75
        }
        return pdrs[(sender, receiver)]

def test_CT(expectedInOut):
    '''
    testing success probability of a packet going through to a moving node from a given
    root node given relays and link PDRs
    '''

    testwireless = TestWireless()
    testwireless.rootNode = 'A'

    assert testwireless._getPdrCT(*expectedInOut['in'].values()) == expectedInOut['out']
