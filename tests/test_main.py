from Wireless import PropagationPister, PropagationRadius

def test_dummy():
    assert 1 + 1 == 2

def test_get_PDR_PH():
    sender   =  (5,5)
    receiver =  (0,3)
    pdr, rssi = PropagationPister().getPDR(sender, receiver, rssi=True)
    assert pdr >= 0 and pdr <= 1

def test_get_PDR_R_success():
    sender   =  (0,0)
    receiver =  (7,7)
    pdr = PropagationRadius().getPDR(sender, receiver)
    assert pdr == 1

def test_get_PDR_R_fail():
    sender   =  (0,0)
    receiver =  (20,15)
    pdr = PropagationRadius().getPDR(sender, receiver)
    assert pdr == 0