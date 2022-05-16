import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # diagonally (45 degree angle) left to right
    {
        'in': {
            'ax':  0.10,
            'ay':  0.10,
            'bx':  1.40,
            'by':  1.40,
        },
        'out': [
            (0.00, 0.00),
            (0.50, 0.50),
            (1.00, 1.00)
        ],
    },

    # diagonally (45 degree angle) right to left
    {
        'in': {
            'ax':  1.40,
            'ay':  1.40,
            'bx':  0.10,
            'by':  0.10,
        },
        'out': [
            (0.00, 0.00),
            (0.50, 0.50),
            (1.00, 1.00)
        ],
    },

    # x increasing, y increasing
    {
        'in': {
            'ax':  3.45,
            'ay':  0.10,
            'bx':  4.25,
            'by':  2.35,
        },
        'out': [
            (3.00, 0.00),
            (3.50, 0.00),
            (3.50, 0.50),
            (3.50, 1.00),
            (3.50, 1.50),
            (4.00, 1.50),
            (4.00, 2.00)
        ],
    },

    # x decreasing, y decreasing
    {
        'in': {
            'ax':  4.25,
            'ay':  2.35,
            'bx':  3.45,
            'by':  0.10,
        },
        'out': [
            (3.00, 0.00),
            (3.50, 0.00),
            (3.50, 0.50),
            (3.50, 1.00),
            (3.50, 1.50),
            (4.00, 1.50),
            (4.00, 2.00)
        ],
    },

    # x decreasing, y increasing
    {
        'in': {
            'ax':  5.25,
            'ay':  1.25,
            'bx':  3.60,
            'by':  2.20,
        },
        'out': [
            (5.00, 1.00),
            (4.50, 1.00),
            (4.50, 1.50),
            (4.00, 1.50),
            (3.50, 1.50),
            (3.50, 2.00)
        ],
    },

    # x increasing, y decreasing
    {
        'in': {
            'ax':  3.60,
            'ay':  2.20,
            'bx':  5.25,
            'by':  1.25,
        },
        'out': [
            (5.00, 1.00),
            (4.50, 1.00),
            (4.50, 1.50),
            (4.00, 1.50),
            (3.50, 1.50),
            (3.50, 2.00)
        ],
    },

    # horizontal line, left to right
    {
        'in': {
            'ax':  1.60,
            'ay':  3.30,
            'bx':  2.70,
            'by':  3.30,
        },
        'out': [
            (1.50, 3.00),
            (2.00, 3.00),
            (2.50, 3.00)
        ],
    },

    # horizontal line, right to left
    {
        'in': {
            'ax':  2.70,
            'ay':  3.30,
            'bx':  1.60,
            'by':  3.30,
        },
        'out': [
            (1.50, 3.00),
            (2.00, 3.00),
            (2.50, 3.00)],
    },

    # vertical line, y increasing
    {
        'in': {
            'ax':  3.81,
            'ay':  3.70,
            'bx':  3.81,
            'by':  5.90,
        },
        'out': [
            (3.50, 3.50),
            (3.50, 4.00),
            (3.50, 4.50),
            (3.50, 5.00),
            (3.50, 5.50)
        ],
    },

    # vertical line, y decreasing
    {
        'in': {
            'ax':  3.81,
            'ay':  5.90,
            'bx':  3.81,
            'by':  3.70,
        },
        'out': [
            (3.50, 3.50),
            (3.50, 4.00),
            (3.50, 4.50),
            (3.50, 5.00),
            (3.50, 5.50)
        ],
    },

    # line within same cell
    {
        'in': {
            'ax': 2.04,
            'ay': 1.52,
            'bx': 2.49,
            'by': 1.67,
        },
        'out': [
            (2.00, 1.50)
        ],
    },

    # two cells next to each other (movement across x cell boundary)
    {
        'in': {
            'ax': 2.00,
            'ay': 1.00,
            'bx': 2.50,
            'by': 1.00,
        },
        'out': [],
    },

    # movement across y cell boundary
    {
        'in': {
            'ax': 1.50,
            'ay': 1.00,
            'bx': 3.00,
            'by': 1.00,
        },
        'out': [],
    },

    # border-to-border, horizontal
    {
        'in': {
            'ax': 2.00,
            'ay': 1.49,
            'bx': 5.00,
            'by': 1.49,
        },
        'out': [
            (2.00, 1.00),
            (2.50, 1.00),
            (3.00, 1.00),
            (3.50, 1.00),
            (4.00, 1.00),
            (4.50, 1.00),
        ],
    },

    # border-to-border, horizontal, single cell
    {
        'in': {
            'ax': 2.00,
            'ay': 1.45,
            'bx': 2.50,
            'by': 1.45,
        },
        'out': [
            (2.00, 1.00),
        ],
    },
    # border-to-border, vertical
    {
        'in': {
            'ax': 1.52,
            'ay': 1.00,
            'bx': 1.52,
            'by': 4.00,
        },
        'out': [
            (1.50, 1.00),
            (1.50, 1.50),
            (1.50, 2.00),
            (1.50, 2.50),
            (1.50, 3.00),
            (1.50, 3.50),
        ],
    },
    # border-to-border, diagonal
    {
        'in': {
            'ax': 2.00,
            'ay': 4.00,
            'bx': 5.00,
            'by': 1.00,
        },
        'out': [

            (2.00, 3.50),
            (2.50, 3.00),
            (3.00, 2.50),
            (3.50, 2.00),
            (4.00, 1.50),
            (4.50, 1.00),
        ],
    },

    # inside cell to top left border
    {
        'in': {
            'ax': 1.6,
            'ay': 1.3,
            'bx': 2.5,
            'by': 2.00,
        },
        'out': [
            (1.50, 1.00),
            (1.50, 1.50),
            (2.00, 1.50),
        ],
    },
]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_computeExploredCells(expectedInOut):
    '''
    testing computation of trajectory of cells created from a line from point a to point b
    '''

    orchestrator = Orchestrator.Orchestrator(1,1,1)
    orchestrator.MINFEATURESIZE = 1

    assert sorted(orchestrator._computeExploredCells(*expectedInOut['in'].values()))==sorted(expectedInOut['out'])

