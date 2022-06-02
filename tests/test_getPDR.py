import Wireless
import pytest
# ============================ fixtures ==============================
EXPECTEDINOUT = [

    {
        'in': {
            'sender':      'A',
            'receiver':    'D',
            'relays':      ['B', 'C'],
        },
        'out': 0.87008
    },
]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param
# ============================ tests =================================

class TestWireless(Wireless.Wireless):
    def __new__(cls):
        return object.__new__(cls)

    def _getStability(self, sender, receiver):
        pdrs = {
            ('A','B'): 0.60,
            ('A','C'): 0.90,
            ('A','D'): 0.20,
            ('B','A'): 0.60,
            ('B','D'): 0.70,
            ('C','A'): 0.90,
            ('C','D'): 0.80,
            ('D','A'): 0.20,
            ('D','B'): 0.70,
            ('D','C'): 0.80
        }
        return pdrs[(sender, receiver)]

def test_CT(expectedInOut):
    '''
    testing success probability of a packet going through to a moving node from a given
    root node given relays and link PDRs
    '''

    testwireless = TestWireless()
    testwireless.rootNode = 'A'

    assert testwireless._getPDR(*expectedInOut['in'].values()) == expectedInOut['out']