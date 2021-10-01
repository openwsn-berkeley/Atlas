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

def test_get_PDR_LOS_success():
    drawing =   '''
##################
#................#
#...########.....#
#................#
##################
'''
    node1   =  (6,2)
    node2   =  (6,4)
    node3   =  (8,2)

    floorplan    = Floorplan(drawing)
    prop_model   = PropagationLOS()
    prop_model.indicateFloorplan(floorplan)
    pdr1 = prop_model.getPDR(node1, node3)
    pdr2 = prop_model.getPDR(node1, node2)
    pdr3 = prop_model.getPDR(node2, node3)
    assert pdr1 == 1 and pdr2 == pdr3 == 0

def test_line_intersect():

    p1 =  PropagationLOS.line_intersection(((0,1),(0,-1)),((1,0),(2,0)))
    assert not p1

    p2 =  PropagationLOS.line_intersection(((0,1),(0,-1)),((-1,0),(1,0)))
    assert p2

    p3 =  PropagationLOS.line_intersection(((2,1),(5,1)),((3,0),(3,1)))
    assert p3

    p4 =  PropagationLOS.line_intersection(((2,1),(5,1)),((3,0),(3,0.5)))
    assert not p4

if __name__ == '__main__':
    test_line_intersect()