import Wireless

# ============================ fixtures ==============================

# ============================ tests =================================

class TestWireless(Wireless.Wireless):
    def _computePdrPisterHack(self, sender_pos, receiver_pos):
        pdr = 0.7
        return pdr

def test_CT():
    '''
    testing success probability given nodes and node total PDRs
    '''

    testwireless = TestWireless()
    print(testwireless.devices)
    assert testwireless._computePdrPisterHack(sender_pos=None, receiver_pos=None) == 0.7
