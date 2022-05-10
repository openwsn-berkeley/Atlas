import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [
    {
        'in': {
            'startX': 0.65,
            'startY': 1.55,
            'stopX':  1.9,
            'stopY':  0.35,
        },
        'out': [(1, 2), (1, 1.5), (1.5, 1.5), (1.5, 1), (2, 1)],
    },
    {
        'in': {
            'startX': 2.3,
            'startY': 0.7,
            'stopX':  3.7,
            'stopY':  0.7,
        },
        'out': [(2.5,1),(3, 1), (3.5, 1)],
    },

    {
        'in': {
            'startX': 3.65,
            'startY': 0.7,
            'stopX':  4.75,
            'stopY':  1.9,
        },
        'out': [(4, 1), (4, 1.5), (4.5, 1.5), (4.5, 2), (5, 2)],
    },
    {
        'in': {
            'startX': 1.75,
            'startY': 3.4,
            'stopX':  0.6,
            'stopY':  2.55,
        },
        'out': [(1, 3), (1.5, 3.5), (1.5, 3), (2, 3.5)],
    },
    {
        'in': {
            'startX': 2.8,
            'startY': 2.4,
            'stopX':  1.3,
            'stopY':  2.4,
        },
        'out': [(1.5, 2.5), (2.5, 2.5), (2, 2.5), (3, 2.5)],
    },
    {
        'in': {
            'startX': 3.8,
            'startY': 2.2,
            'stopX':  2.6,
            'stopY':  3.45,
        },
        'out': [(3,3.5), (3, 3), (3.5, 3), (3.5, 2.5), (4, 2.5)],
    },
    {
        'in': {
            'startX': 0.3,
            'startY': 3.7,
            'stopX':  0.3,
            'stopY':  2.7,
        },
        'out': [(0.5, 4), (0.5, 3.5), (0.5, 3)],
    },
    {
        'in': {
            'startX': 4.65,
            'startY': 2.6,
            'stopX':  4.65,
            'stopY':  3.7,
        },
        'out': [(5,3), (5, 3.5), (5, 4)],
    },
    {
        'in': {
            'startX': 41.97,
            'startY': 0,
            'stopX':  38.9,
            'stopY':  10,
        },
        'out': [(39, 9.5), (39.5, 9.5), (39.5, 9.0), (39.5, 8.5), (39.5, 8.0), (40, 8.0),
                (40, 7.5), (40, 7.0), (40, 6.5), (40, 6.0), (40.5, 6.0), (40.5, 5.5),
                (40.5, 5.0), (40.5, 4.5), (41, 4.5), (41, 4.0), (41, 3.5), (41, 3.0),
                (41.5, 3.0), (41.5, 2.5), (41.5, 2.0), (41.5, 1.5), (42, 1.5), (42, 1.0),
                (42, 0.5)],
    },
    {
        'in': {
            'startX': 0.25,
            'startY': 1.25,
            'stopX':  1.65,
            'stopY':  1.8,
        },
        'out': [(0.5, 1.5), (1,1.5), (1, 2), (1.5, 2)],
    },
    {
        'in': {
            'startX': 0.25,
            'startY': 1.4,
            'stopX':  1.7,
            'stopY':  0.2,
        },
        'out': [(0.5, 1.5), (1,2), (1,1.5), (1.5,1), (1.5, 0.5)],
    },

]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_cellsTraversed(expectedInOut):

    orchestrator = Orchestrator.Orchestrator(1,0,0)
    startX = expectedInOut['in']['startX']
    startY = expectedInOut['in']['startY']
    stopX  = expectedInOut['in']['stopX']
    stopY  = expectedInOut['in']['stopY']
    orchestrator.MINFEATURESIZE = 1

    output = orchestrator._cellsTraversed(startX, startY, stopX, stopY )
    assert len(output) == len(expectedInOut['out'])
    for i in output:
        assert i in expectedInOut['out']

