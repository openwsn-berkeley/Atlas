import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [
    {
        'in': {
            'startX': 0.1,
            'startY': 0.1,
            'stopX':  1.4,
            'stopY':  1.4,
        },
        'out': [(0,0), (0.5,0.5), (1, 1)],
    },
    {
        'in': {
            'startX': 1.4,
            'startY': 1.4,
            'stopX':  0.1,
            'stopY':  0.1,
        },
        'out': [(0,0), (0.5,0.5), (1, 1)],
    },

    {
        'in': {
            'startX': 3.45,
            'startY': 0.1,
            'stopX':  4.25,
            'stopY':  2.35,
        },
        'out': [(3,0), (3.5, 0), (3.5, 0.5), (3.5, 1), (3.5, 1.5), (4, 1.5), (4, 2)],
    },
    {
        'in': {
            'startX': 4.25,
            'startY': 2.35,
            'stopX':  3.45,
            'stopY':  0.1,
        },
        'out': [(3,0), (3.5, 0), (3.5, 0.5), (3.5, 1), (3.5, 1.5), (4, 1.5), (4, 2)],
    },
    {
        'in': {
            'startX': 5.25,
            'startY': 1.25,
            'stopX':  3.6,
            'stopY':  2.2,
        },
        'out': [(5, 1), (4.5, 1), (4.5, 1.5), (4, 1.5), (3.5, 1.5), (3.5, 2)],
    },
    {
        'in': {
            'startX': 3.6,
            'startY': 2.2,
            'stopX':  5.25,
            'stopY':  1.25,
        },
        'out': [(5, 1), (4.5, 1), (4.5, 1.5), (4, 1.5), (3.5, 1.5), (3.5, 2)],
    },
    {
        'in': {
            'startX': 1.6,
            'startY': 3.3,
            'stopX':  2.7,
            'stopY':  3.3,
        },
        'out': [ (1.5, 3), (2, 3), (2.5, 3)],
    },
    {
        'in': {
            'startX': 2.7,
            'startY': 3.3,
            'stopX':  1.6,
            'stopY':  3.3,
        },
        'out': [(1.5, 3), (2, 3), (2.5, 3)],
    },

    {
        'in': {
            'startX': 3.81,
            'startY': 3.702,
            'stopX':  3.81,
            'stopY':  5.9,
        },
        'out': [(3.5, 3.5), (3.5, 4), (3.5, 4.5), (3.5, 5), (3.5, 5.5)],
    },
    {
        'in': {
            'startX': 3.81,
            'startY': 5.9,
            'stopX': 3.81,
            'stopY': 3.702,
        },
        'out': [(3.5, 3.5), (3.5, 4), (3.5, 4.5), (3.5, 5), (3.5, 5.5)],
    },
    {
        'in': {
            'startX': 2.0412,
            'startY': 1.52,
            'stopX': 2.499,
            'stopY': 1.67,
        },
        'out': [(2, 1.5)],
    },
    {
        'in': {
            'startX': 2,
            'startY': 1,
            'stopX': 2.5,
            'stopY': 1,
        },
        'out': [(2, 1), (2.5, 1)],
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

