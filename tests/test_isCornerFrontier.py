import Floorplan
import Orchestrator
import pytest

# ============================ fixtures ==============================

EXPECTEDINOUT = [

    # one obstacle only
    {
        'in': {
            'cell': (0.50, 0.50)
        },
        'out': False
    },

    # two horizontal obstacles
    {
        'in': {
            'cell': (2.00, 0.50)
        },
        'out': False
    },

    # two diagonal obstacles to the right, frontier to the right
    {
        'in': {
            'cell': (6.00, 0.50)
        },
        'out': True
    },

    # two diagonal obstacles no explored cell connected
    {
        'in': {
            'cell': (2.00, 3.00)
        },
        'out': False
    },

    # two diagonal obstacles to the left
    {
        'in': {
            'cell': (3.50, 2.50)
        },
        'out': True
    },

    # two diagonal obstacles to the right, frontier to the left
    {
        'in': {
            'cell': (0.50, 5.00)
        },
        'out': True
    },
]

@pytest.fixture(params=EXPECTEDINOUT)
def expectedInOut(request):
    return request.param

# ============================ tests =================================

def test_isCornerFrontier(expectedInOut):
    '''
    testing if corner cells are identified correctly
    '''

    orchestrator  = Orchestrator.Orchestrator(
        numRobots = 1,
        initX     = 1,
        initY     = 1
    )
    orchestrator.MINFEATURESIZE = 1
    orchestrator.cellsExplored = [(1,1), (1.5,1),(2,1),(5.5,1),(4,3),(1,4.5)]
    orchestrator.cellsObstacle = [(1.0,0.5),(1.5,0.5),(5.5,0.5),(6,1),(4,2.5),(3.5,3),(2.5,3),(2,3.5),(0.5,4.5),(1,5)]

    assert orchestrator._isCornerFrontier(*expectedInOut['in'].values()) == expectedInOut['out']