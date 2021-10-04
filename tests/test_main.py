from Wireless import PropagationPister, PropagationRadius, PropagationFriis, PropagationLOS
from Floorplan import Floorplan
def test_dummy():
    assert 1 + 1 == 2

def test_get_PDR_PH():
    sender   =  (5,5)
    receiver =  (0,3)
    pdr = PropagationPister().getPDR(sender, receiver)
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

def test_get_PDR_Friis():
    sender   =  (5,5)
    receiver =  (0,3)
    pdr = PropagationFriis().getPDR(sender, receiver)
    assert pdr >= 0 and pdr <= 1

def test_get_PDR_LOS():
    drawing =   '''
##################
#................#
#...########..#..#
#................#
##################
'''
    node1   =  (6,2)
    node2   =  (6,4)
    node3   =  (8,2)
    node4   =  (4,2.5)
    node5   =  (13,2.5)
    node6   =  (16,2.5)
    node7   =  (4,2)
    node8   =  (3,3)

    floorplan    = Floorplan(drawing)
    prop_model   = PropagationLOS()
    prop_model.indicateFloorplan(floorplan)

    pdr1 = prop_model.getPDR(node1, node3)
    pdr2 = prop_model.getPDR(node1, node2)
    pdr3 = prop_model.getPDR(node2, node3)
    assert pdr1 == 1 and pdr2 == pdr3 == 0
    pdr4 = prop_model.getPDR(node4, node5)
    pdr5 = prop_model.getPDR(node5, node6)
    pdr6 = prop_model.getPDR(node4, node6)
    assert pdr4 == pdr5 == pdr6 == 0
    pdr7 = prop_model.getPDR(node7, node8)
    assert pdr7 == 1

if __name__ == '__main__':
    test_get_PDR_LOS()