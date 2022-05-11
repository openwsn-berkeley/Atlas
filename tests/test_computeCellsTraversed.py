import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # diagonally (45 degree angle) left to right
    {
        'in': {
            'ax':  0.1,
            'ay':  0.1,
            'bx':  1.4,
            'by':  1.4,
        },
        'out': [(0,0), (0.5,0.5), (1, 1)],
    },

    # diagonally (45 degree angle) right to left
    {
        'in': {
            'ax':  1.4,
            'ay':  1.4,
            'bx':  0.1,
            'by':  0.1,
        },
        'out': [(0,0), (0.5,0.5), (1, 1)],
    },

    # x increasing, y increasing
    {
        'in': {
            'ax':  3.45,
            'ay':  0.1,
            'bx':  4.25,
            'by':  2.35,
        },
        'out': [(3,0), (3.5, 0), (3.5, 0.5), (3.5, 1), (3.5, 1.5), (4, 1.5), (4, 2)],
    },

    # x decreasing, y decreasing
    {
        'in': {
            'ax':  4.25,
            'ay':  2.35,
            'bx':  3.45,
            'by':  0.1,
        },
        'out': [(3, 0), (3.5, 0), (3.5, 0.5), (3.5, 1), (3.5, 1.5), (4, 1.5), (4, 2)],
    },

    # x decreasing, y increasing
    {
        'in': {
            'ax':  5.25,
            'ay':  1.25,
            'bx':  3.6,
            'by':  2.2,
        },
        'out': [(5, 1), (4.5, 1), (4.5, 1.5), (4, 1.5), (3.5, 1.5), (3.5, 2)],
    },

    # x increasing, y decreasing
    {
        'in': {
            'ax':  3.6,
            'ay':  2.2,
            'bx':  5.25,
            'by':  1.25,
        },
        'out': [(5, 1), (4.5, 1), (4.5, 1.5), (4, 1.5), (3.5, 1.5), (3.5, 2)],
    },

    # horizontal line, left to right
    {
        'in': {
            'ax':  1.6,
            'ay':  3.3,
            'bx':  2.7,
            'by':  3.3,
        },
        'out': [(1.5, 3), (2, 3), (2.5, 3)],
    },

    # horizontal line, right to left
    {
        'in': {
            'ax':  2.7,
            'ay':  3.3,
            'bx':  1.6,
            'by':  3.3,
        },
        'out': [(1.5, 3), (2, 3), (2.5, 3)],
    },

    # vertical line, y increasing
    {
        'in': {
            'ax':  3.81,
            'ay':  3.702,
            'bx':  3.81,
            'by':  5.9,
        },
        'out': [(3.5, 3.5), (3.5, 4), (3.5, 4.5), (3.5, 5), (3.5, 5.5)],
    },

    # vertical line, y decreasing
    {
        'in': {
            'ax':  3.81,
            'ay':  5.9,
            'bx':  3.81,
            'by':  3.702,
        },
        'out': [(3.5, 3.5), (3.5, 4), (3.5, 4.5), (3.5, 5), (3.5, 5.5)],
    },

    # line within same cell
    {
        'in': {
            'ax': 2.0412,
            'ay': 1.52,
            'bx': 2.499,
            'by': 1.67,
        },
        'out': [(2, 1.5)],
    },

    # two cells next to each other (movement across cell boundary)
    {
        'in': {
            'ax': 2,
            'ay': 1,
            'bx': 2.5,
            'by': 1,
        },
        'out': [(2, 1), (2.5, 1)],
    },

]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_computeCellsTraversed(expectedInOut):
    '''
    testing computation of trajectory of cells created from a line from point a to point b
    '''

    orchestrator = Orchestrator.Orchestrator(1,1,1)
    orchestrator.MINFEATURESIZE = 1

    output = orchestrator._computeCellsTraversed(*expectedInOut['in'].values() )
    assert len(output) == len(expectedInOut['out'])
    for i in output:
        assert i in expectedInOut['out']

