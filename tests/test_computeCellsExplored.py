import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # diagonally (45 degree angle) left to right
    {
        'in': {
            'startX':  0.10,
            'startY':  0.10,
            'stopX':   1.40,
            'stopY':   1.40,
        },
        'out': {
            'cellsExplored': [
                (0.00, 0.00),
                (0.50, 0.50),
                (1.00, 1.00)
            ],
            'nextCell': (1.50, 1.50)
        }
    },

    # diagonally (45 degree angle) right to left
    {
        'in': {
            'startX':  1.40,
            'startY':  1.40,
            'stopX':   0.10,
            'stopY':   0.10,
        },
        'out': {
            'cellsExplored': [
                (0.00, 0.00),
                (0.50, 0.50),
                (1.00, 1.00)
            ],
            'nextCell': (-0.50, -0.50)
        }
    },

    # x increasing, y increasing
    {
        'in': {
            'startX':  3.45,
            'startY':  0.10,
            'stopX':   4.25,
            'stopY':   2.35,
        },
        'out': {
            'cellsExplored': [
                (3.00, 0.00),
                (3.50, 0.00),
                (3.50, 0.50),
                (3.50, 1.00),
                (3.50, 1.50),
                (4.00, 1.50),
                (4.00, 2.00)
            ],
            'nextCell': (4.00, 2.50)
        }
    },

    # x decreasing, y decreasing
    {
        'in': {
            'startX':  4.25,
            'startY':  2.35,
            'stopX':   3.45,
            'stopY':   0.10,
        },
        'out': {
            'cellsExplored': [
                (3.00, 0.00),
                (3.50, 0.00),
                (3.50, 0.50),
                (3.50, 1.00),
                (3.50, 1.50),
                (4.00, 1.50),
                (4.00, 2.00)
            ],
            'nextCell': (3.00, -0.50)
        }
    },

    # x decreasing, y increasing
    {
        'in': {
            'startX':  5.25,
            'startY':  1.25,
            'stopX':   3.60,
            'stopY':   2.20,
        },
        'out': {
            'cellsExplored': [
                (5.00, 1.00),
                (4.50, 1.00),
                (4.50, 1.50),
                (4.00, 1.50),
                (3.50, 1.50),
                (3.50, 2.00)
            ],
            'nextCell': (3.00, 2.00)
        }
    },

    # x increasing, y decreasing
    {
        'in': {
            'startX':  3.60,
            'startY':  2.20,
            'stopX':   5.25,
            'stopY':   1.25,
        },
        'out': {
            'cellsExplored' : [
                (5.00, 1.00),
                (4.50, 1.00),
                (4.50, 1.50),
                (4.00, 1.50),
                (3.50, 1.50),
                (3.50, 2.00)
            ],
            'nextCell' : (5.50, 1.00)
        }
    },

    # horizontal line, left to right
    {
        'in': {
            'startX':  1.60,
            'startY':  3.30,
            'stopX':   2.70,
            'stopY':   3.30,
        },
        'out': {
            'cellsExplored': [
                (1.50, 3.00),
                (2.00, 3.00),
                (2.50, 3.00)
            ],
            'nextCell' : (3.00, 3.00)
        }
    },

    # horizontal line, right to left
    {
        'in': {
            'startX':  2.70,
            'startY':  3.30,
            'stopX':   1.60,
            'stopY':   3.30,
        },
        'out': {
            'cellsExplored': [
                (1.50, 3.00),
                (2.00, 3.00),
                (2.50, 3.00)
            ],
            'nextCell': (1.00, 3.00)
        }
    },

    # vertical line, y increasing
    {
        'in': {
            'startX':  3.81,
            'startY':  3.70,
            'stopX':   3.81,
            'stopY':   5.90,
        },
        'out': {
            'cellsExplored': [
                (3.50, 3.50),
                (3.50, 4.00),
                (3.50, 4.50),
                (3.50, 5.00),
                (3.50, 5.50)
            ],
            'nextCell': (3.50, 6.00)
        }
    },

    # vertical line, y decreasing
    {
        'in': {
            'startX':  3.81,
            'startY':  5.90,
            'stopX':   3.81,
            'stopY':   3.70,
        },
        'out': {
            'cellsExplored': [
                (3.50, 3.50),
                (3.50, 4.00),
                (3.50, 4.50),
                (3.50, 5.00),
                (3.50, 5.50)
            ],
            'nextCell': (3.50, 3.00)
        }
    },

    # line within same cell
    {
        'in': {
            'startX': 2.04,
            'startY': 1.52,
            'stopX':  2.49,
            'stopY':  1.67,
        },
        'out': {
            'cellsExplored': [
                (2.00, 1.50)
            ],
            'nextCell': (2.50, 1.50)
        }
    },

    # two cells next to each other (movement across x cell boundary)
    {
        'in': {
            'startX': 2.00,
            'startY': 1.00,
            'stopX':  2.50,
            'stopY':  1.00,
        },
        'out': {
            'cellsExplored': [],
            'nextCell':      None
        }
    },

    # movement across y cell boundary
    {
        'in': {
            'startX': 1.50,
            'startY': 1.00,
            'stopX':  3.00,
            'stopY':  1.00,
        },
        'out': {
            'cellsExplored': [],
            'nextCell':      None
        }
    },

    # border-to-border, horizontal
    {
        'in': {
            'startX': 2.00,
            'startY': 1.49,
            'stopX':  5.00,
            'stopY':  1.49,
        },
        'out': {
            'cellsExplored': [
                (2.00, 1.00),
                (2.50, 1.00),
                (3.00, 1.00),
                (3.50, 1.00),
                (4.00, 1.00),
                (4.50, 1.00),
            ],
            'nextCell': (5.00, 1.00)
        }
    },

    # border-to-border, horizontal, single cell
    {
        'in': {
            'startX': 2.00,
            'startY': 1.45,
            'stopX':  2.50,
            'stopY':  1.45,
        },
        'out': {
            'cellsExplored': [
                (2.00, 1.00),
            ],
            'nextCell': (2.50, 1.00)
        }
    },
    # border-to-border, vertical
    {
        'in': {
            'startX': 1.52,
            'startY': 1.00,
            'stopX':  1.52,
            'stopY':  4.00,
        },
        'out': {
            'cellsExplored': [
                (1.50, 1.00),
                (1.50, 1.50),
                (1.50, 2.00),
                (1.50, 2.50),
                (1.50, 3.00),
                (1.50, 3.50),
            ],
            'nextCell': (1.50, 4.00)
        }
    },
    # border-to-border, diagonal
    {
        'in': {
            'startX': 2.00,
            'startY': 4.00,
            'stopX':  5.00,
            'stopY':  1.00,
        },
        'out': {
            'cellsExplored': [
                (2.00, 3.50),
                (2.50, 3.00),
                (3.00, 2.50),
                (3.50, 2.00),
                (4.00, 1.50),
                (4.50, 1.00),
            ],
            'nextCell': None
        }
    },

    # inside cell to top left border
    {
        'in': {
            'startX': 1.6,
            'startY': 1.3,
            'stopX':  2.5,
            'stopY':  2.00,
        },
        'out': {
            'cellsExplored': [
                (1.50, 1.00),
                (1.50, 1.50),
                (2.00, 1.50),
            ],
            'nextCell': None
        }
    },

    # left border to centre of next cell
    {
        'in': {
            'startX': 5.0,
            'startY': 4.75,
            'stopX':  5.75,
            'stopY':  4.75,
        },
        'out': {
            'cellsExplored': [
                (5.00, 4.50),
                (5.50, 4.50)
            ],
            'nextCell': (6.00, 4.50)
        }
    },
]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_computeCellsExplored(expectedInOut):
    '''
    testing computation of trajectory of cells created from a line from point a to point b
    and next cell beyond that
    '''

    orchestrator = Orchestrator.Orchestrator(1, 1, 1)
    output       = orchestrator._computeCellsExplored(*expectedInOut['in'].values())
    assert sorted(output['cellsExplored']) == sorted(expectedInOut['out']['cellsExplored'])
    assert output['nextCell']              == expectedInOut['out']['nextCell']


