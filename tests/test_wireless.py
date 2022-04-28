import Wireless

def test_get_PDR_PH():
    sender   =  (5,5)
    receiver =  (0,3)
    pdr = Wireless.PropagationPisterHack().getPDR(sender, receiver)
    assert pdr >= 0 and pdr <= 1

def test_get_PDR_R_success():
    sender   =  (0,0)
    receiver =  (7,7)
    pdr = Wireless.PropagationRadius(radius=10).getPDR(sender, receiver)
    assert pdr == 1

def test_get_PDR_R_fail():
    sender   =  (0,0)
    receiver =  (20,15)
    pdr = Wireless.PropagationRadius().getPDR(sender, receiver)
    assert pdr == 0

def test_get_PDR_Friis():
    sender   =  (5,5)
    receiver =  (0,3)
    pdr = Wireless.PropagationFriis().getPDR(sender, receiver)
    assert pdr >= 0 and pdr <= 1


def test_line_intersect_simple():
    obstacle_line = ((0, -1), (0, 1))

    p1 =  Wireless.PropagationLOS.line_intersection(((1, 0), (2, 0)), obstacle_line)
    assert not p1

    p2 =  Wireless.PropagationLOS.line_intersection(((-1, 0), (1, 0)), obstacle_line)
    assert p2

    p3 =  Wireless.PropagationLOS.line_intersection(((0, 0), (1, 0)), obstacle_line)
    assert not p3

    p4 =  Wireless.PropagationLOS.line_intersection(((0, -1.5), (0, 1.5)), obstacle_line)
    assert p4

def test_line_intersect():
    p1 =  Wireless.PropagationLOS.line_intersection(((0,1),(0,-1)),((1,0),(2,0)))
    assert not p1

    p2 =  Wireless.PropagationLOS.line_intersection(((0,1),(0,-1)),((-1,0),(1,0)))
    assert p2

    p3 =  Wireless.PropagationLOS.line_intersection(((2,1),(5,1)),((3,0),(3,1)))
    assert p3

    p4 =  Wireless.PropagationLOS.line_intersection(((2,1),(5,1)),((3,0),(3,0.5)))
    assert not p4